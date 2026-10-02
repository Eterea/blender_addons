# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Cristobal Vila (etereaestudios.com)

"""
Round Values

Available in the 3D Viewport Object > Transform menu and also in the shared
"Eterea Tools" submenu of the 3D Viewport (Object Mode) and Outliner
right-click menus (see eterea_ui.py).

The thresholds (1e-4 by default) are set in the add-on Preferences, section
"Round Values". They are always in Blender internal units (metres for
location, degrees for rotation, plain factor for scale), independent of the
scene unit system. Euler, Quaternion and Axis Angle rotation modes are all
supported.
"""

bl_info = {
    "name": "Round Values",
    "author": "Idea by Cristobal Vila / Code by Claude.ai",
    "version": (1, 5, 0),
    "blender": (5, 2, 0),
    "location": (
        "3D Viewport > Object > Transform > Round values to 0 or 1; "
        "3D Viewport / Outliner > Right-Click > Eterea Tools"
    ),
    "description": (
        "Round near-zero location/rotation channels to 0 and near-unit scale "
        "channels to +/-1 on the selected objects."
    ),
    "category": "Object",
}

import bpy
import math

from bpy.props import FloatProperty

from . import eterea_ui


# ---------------------------------------------------------------------------
# Default thresholds (editable in the Preferences)
# ---------------------------------------------------------------------------

# Location: 1e-4 in Blender internal units (metres), always.
# obj.location is always stored in internal units regardless of the scene
# unit system, so we must NOT multiply by unit_settings.scale_length.
# Doing so shrank the threshold to 1e-6 for cm scenes and 1e-7 for mm scenes,
# which caused near-zero values like 0.000012 to be silently skipped.
DEFAULT_LOCATION_THRESHOLD = 1e-4

# Rotation: 1e-4 degrees (converted to radians when used).
DEFAULT_ROTATION_THRESHOLD_DEG = 1e-4

# Scale: dimensionless, so no unit conversion needed.
DEFAULT_SCALE_THRESHOLD = 1e-4


# ---------------------------------------------------------------------------
# Preferences data (registered by preferences.py, which owns the single
# AddonPreferences class of the kit)
# ---------------------------------------------------------------------------

class RoundValuesSettings(bpy.types.PropertyGroup):
    location_threshold: FloatProperty(
        name="Location (m)",
        description=(
            "Location values closer to 0 than this are set to 0. Always in "
            "Blender internal units (metres), whatever the scene unit system"
        ),
        default=DEFAULT_LOCATION_THRESHOLD,
        min=0.0,
        soft_max=0.01,
        precision=6,
        step=1,
    )
    rotation_threshold: FloatProperty(
        name="Rotation (degrees)",
        description="Rotation values closer to 0 degrees than this are set to 0",
        default=DEFAULT_ROTATION_THRESHOLD_DEG,
        min=0.0,
        soft_max=1.0,
        precision=6,
        step=1,
    )
    scale_threshold: FloatProperty(
        name="Scale",
        description="Scale values closer to 1 (or -1) than this are set to 1 (or -1)",
        default=DEFAULT_SCALE_THRESHOLD,
        min=0.0,
        soft_max=0.01,
        precision=6,
        step=1,
    )


def get_settings(context=None):
    """Return this tool's settings from the add-on Preferences, or None."""
    # Imported here: preferences.py imports this module at load time.
    from . import preferences

    prefs = preferences.get_preferences(context)
    return getattr(prefs, "round_values", None)


def get_thresholds(context=None):
    """Return (location, rotation in radians, scale) thresholds.

    Falls back to the defaults if the Preferences are not available.
    """
    settings = get_settings(context)
    if settings is None:
        return (
            DEFAULT_LOCATION_THRESHOLD,
            math.radians(DEFAULT_ROTATION_THRESHOLD_DEG),
            DEFAULT_SCALE_THRESHOLD,
        )
    return (
        settings.location_threshold,
        math.radians(settings.rotation_threshold),
        settings.scale_threshold,
    )


# ---------------------------------------------------------------------------
# Core rounding logic
# ---------------------------------------------------------------------------

def _round_location(obj, threshold):
    changes = 0
    loc = obj.location
    for i in range(3):
        if abs(loc[i]) <= threshold and loc[i] != 0.0:
            loc[i] = 0.0
            changes += 1
    return changes


def _round_rotation_euler(obj, threshold):
    changes = 0
    rot = obj.rotation_euler
    for i in range(3):
        if abs(rot[i]) <= threshold and rot[i] != 0.0:
            rot[i] = 0.0
            changes += 1
    return changes


def _round_rotation_quaternion(obj, threshold):
    euler = obj.rotation_quaternion.to_euler()
    changed = False
    for i in range(3):
        if abs(euler[i]) <= threshold and euler[i] != 0.0:
            euler[i] = 0.0
            changed = True
    if changed:
        obj.rotation_quaternion = euler.to_quaternion()
        return 1
    return 0


def _round_rotation_axis_angle(obj, threshold):
    # rotation_axis_angle[0] is the angle (radians); [1-3] are the axis vector.
    if abs(obj.rotation_axis_angle[0]) <= threshold \
            and obj.rotation_axis_angle[0] != 0.0:
        obj.rotation_axis_angle[0] = 0.0
        return 1
    return 0


def _round_scale(obj, threshold):
    changes = 0
    scale = obj.scale
    for i in range(3):
        v = scale[i]
        if abs(v - 1.0) <= threshold and v != 1.0:
            scale[i] = 1.0
            changes += 1
        elif abs(v + 1.0) <= threshold and v != -1.0:
            scale[i] = -1.0
            changes += 1
    return changes


def round_object_transforms(obj, thresholds):
    """Round the transforms of `obj`. Return the number of channels changed.

    `thresholds` is (location, rotation in radians, scale), see get_thresholds().
    """
    loc_threshold, rot_threshold, scale_threshold = thresholds
    if obj.rotation_mode == 'QUATERNION':
        rotation = _round_rotation_quaternion(obj, rot_threshold)
    elif obj.rotation_mode == 'AXIS_ANGLE':
        rotation = _round_rotation_axis_angle(obj, rot_threshold)
    else:
        rotation = _round_rotation_euler(obj, rot_threshold)
    return {
        "location": _round_location(obj, loc_threshold),
        "rotation": rotation,
        "scale": _round_scale(obj, scale_threshold),
    }


# ---------------------------------------------------------------------------
# Operator
# ---------------------------------------------------------------------------

class OBJECT_OT_etr_round_values(bpy.types.Operator):
    """Round near-zero location/rotation channels to 0 and near-unit scale to +/-1"""
    bl_idname = "object.etr_round_values"
    bl_label = "Round values to 0 or 1"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and bool(context.selected_objects)

    def execute(self, context):
        total_loc = total_rot = total_scale = 0
        thresholds = get_thresholds(context)

        for obj in context.selected_objects:
            res = round_object_transforms(obj, thresholds)
            total_loc += res["location"]
            total_rot += res["rotation"]
            total_scale += res["scale"]

        total = total_loc + total_rot + total_scale

        # The numbers are counts of channels (not distances), so no unit is
        # shown next to them.
        if total == 0:
            self.report({'INFO'}, "No values needed rounding")
        else:
            self.report(
                {'INFO'},
                f"Rounded {total} channel(s) in "
                f"{len(context.selected_objects)} object(s): "
                f"location {total_loc}, rotation {total_rot}, scale {total_scale}",
            )
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Menu integration
#
# Transform sub-menu names by Blender version:
#   VIEW3D_MT_transform_object  — Blender 5.x  (confirmed)
#   VIEW3D_MT_object_transform  — Blender 2.8x – 4.1
#
# The list is probed in order; the first match wins.
# If none is found (future-proofing), a minimal sub-menu is created and
# appended directly to VIEW3D_MT_object.
# ---------------------------------------------------------------------------

_TRANSFORM_MENU_CANDIDATES = [
    "VIEW3D_MT_transform_object",   # Blender 5.x
    "VIEW3D_MT_object_transform",   # Blender 2.8x – 4.x
]

_hooked_menu_type = None
_hooked_draw_fn = None


def _menu_draw_in_transform(self, context):
    self.layout.operator("object.etr_round_values", icon='SNAP_GRID')


def _menu_draw_in_object(self, context):
    self.layout.separator()
    self.layout.menu(ETR_MT_object_transform_submenu.bl_idname,
                     icon='OBJECT_ORIGIN')


class ETR_MT_object_transform_submenu(bpy.types.Menu):
    """Fallback Transform sub-menu (used only if no built-in one is found)."""
    bl_idname = "ETR_MT_object_transform_submenu"
    bl_label = "Transform"

    def draw(self, context):
        self.layout.operator("object.etr_round_values", icon='SNAP_GRID')


class OBJECT_OT_etr_round_values_reset_settings(bpy.types.Operator):
    bl_idname = "object.etr_round_values_reset_settings"
    bl_label = "Reset Values"
    bl_description = "Restore the default thresholds (0.0001) of Round Values"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return get_settings(context) is not None

    def execute(self, context):
        settings = get_settings(context)
        for name in ("location_threshold", "rotation_threshold", "scale_threshold"):
            settings.property_unset(name)
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Preferences UI (section of the kit Preferences, see preferences.py)
# ---------------------------------------------------------------------------

def draw_preferences(layout, context):
    settings = get_settings(context)
    if settings is None:
        layout.label(text="Preferences not available.", icon='ERROR')
        return

    layout.label(text="Thresholds (values closer than this are rounded):")
    row = layout.row()
    row.alignment = 'LEFT'
    col = row.column(align=True)
    col.ui_units_x = 12
    col.prop(settings, "location_threshold")
    col.prop(settings, "rotation_threshold")
    col.prop(settings, "scale_threshold")
    col.separator()
    col.operator(OBJECT_OT_etr_round_values_reset_settings.bl_idname, icon='LOOP_BACK')

    layout.separator()
    help_col = layout.column(align=True)
    help_col.label(text="Location and rotation are rounded to 0, scale to 1 or -1.", icon='INFO')
    help_col.label(text="Location is always in Blender internal units (metres), even if the scene", icon='BLANK1')
    help_col.label(text="uses centimetres or millimetres (Scene Properties > Units).", icon='BLANK1')


# ---------------------------------------------------------------------------
# "Eterea Tools" submenu section (see eterea_ui.py)
# ---------------------------------------------------------------------------

# Both the 3D Viewport (Object Mode) and the Outliner right-click menus.
_CONTEXTS = (
    eterea_ui.OBJECT_CONTEXT,
    eterea_ui.OUTLINER_CONTEXT,
)


def poll_eterea_tools_section(context):
    """Only show the item in Object Mode with at least one selected object."""
    return context.mode == 'OBJECT' and bool(context.selected_objects)


def draw_eterea_tools_section(layout, context):
    layout.operator("object.etr_round_values", icon='SNAP_GRID')


# ---------------------------------------------------------------------------
# Register / Unregister
# ---------------------------------------------------------------------------

classes = (
    OBJECT_OT_etr_round_values,
    OBJECT_OT_etr_round_values_reset_settings,
)

# Registered only when no built-in Transform menu is found (see register()).
_fallback_menu_registered = False


def register():
    global _hooked_menu_type, _hooked_draw_fn, _fallback_menu_registered

    from . import preferences

    for cls in classes:
        bpy.utils.register_class(cls)

    preferences.add_section("round_values", "Round Values", draw_preferences)

    for context_id in _CONTEXTS:
        eterea_ui.add_section(
            context_id,
            __name__,
            draw_eterea_tools_section,
            poll_eterea_tools_section,
        )

    for candidate in _TRANSFORM_MENU_CANDIDATES:
        menu_type = getattr(bpy.types, candidate, None)
        if menu_type is not None:
            menu_type.append(_menu_draw_in_transform)
            _hooked_menu_type = menu_type
            _hooked_draw_fn = _menu_draw_in_transform
            return

    # Ultimate fallback: attach our own sub-menu to the Object menu.
    bpy.utils.register_class(ETR_MT_object_transform_submenu)
    _fallback_menu_registered = True
    bpy.types.VIEW3D_MT_object.append(_menu_draw_in_object)
    _hooked_menu_type = bpy.types.VIEW3D_MT_object
    _hooked_draw_fn = _menu_draw_in_object


def unregister():
    global _hooked_menu_type, _hooked_draw_fn, _fallback_menu_registered
    from . import preferences

    preferences.remove_section("round_values")

    for context_id in _CONTEXTS:
        eterea_ui.remove_section(context_id, __name__)

    if _hooked_menu_type is not None and _hooked_draw_fn is not None:
        try:
            _hooked_menu_type.remove(_hooked_draw_fn)
        except Exception:
            pass
        _hooked_menu_type = None
        _hooked_draw_fn = None

    if _fallback_menu_registered:
        bpy.utils.unregister_class(ETR_MT_object_transform_submenu)
        _fallback_menu_registered = False

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
