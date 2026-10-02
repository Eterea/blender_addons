# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Cristobal Vila (etereaestudios.com)

"""
Reset Active Modifier to Defaults

Two ways to use it:
  - Panel "Reset Modifier" (3D Viewport > Sidebar > Eterea Tools), showing the
    active modifier of the active object and a "Reset Modifier to Defaults"
    button.
  - Right-click on any parameter of a modifier (Properties > Modifiers) >
    "Reset Modifier to Defaults": resets that modifier, active or not. (The
    modifier's own header menu, the down arrow, is drawn by Blender in C and
    cannot be extended by add-ons, so the right-click menu is used instead.)

How the defaults are found: a temporary modifier of the same type is added to
the object (with the same node group, for Geometry Nodes), its values are
copied to the active modifier, and the temporary modifier is removed. This
gives the real defaults of a freshly added modifier, which do not always match
the RNA defaults (e.g. Mirror's X axis is on for a new modifier, but off in
RNA). If the temporary modifier cannot be added (e.g. physics modifiers, which
are unique per object), the RNA defaults are used instead.

What is reset:
  - Every editable parameter of the modifier, including array/vector ones
    (Mirror axes, Array offsets...).
  - For Geometry Nodes: every exposed input (value, Value/Attribute mode and
    attribute name), back to the defaults defined in the node group.

What is kept:
  - The name, the header toggles (viewport, render, edit mode, on cage,
    apply on spline), the "pin to last" state and other UI states (panel
    expanded, sub-panels open...).
  - Object / data-block references of the modifier itself (Mirror object,
    Boolean object, the node group of a Geometry Nodes modifier...), and
    binding matrices (Hook).
  - Geometry Nodes bake settings.
"""

bl_info = {
    "name": "Reset Active Modifier to Defaults",
    "author": "Idea by Cristobal Vila / Code by Claude.ai",
    "version": (1, 3, 0),
    "blender": (5, 2, 0),
    "location": (
        "3D Viewport > Sidebar (N) > Eterea Tools; "
        "Properties > Modifiers > Right-Click on any parameter"
    ),
    "description": (
        "Reset every parameter of the active modifier (including Geometry Nodes "
        "inputs) to its default value."
    ),
    "category": "Object",
}

import re

import bpy

from . import eterea_ui


# ------------------------------------------------------------
# Reset logic
# ------------------------------------------------------------

# Properties that are never reset: identity, header toggles and UI states.
EXCLUDED_PROPS = {
    "rna_type",
    "name",
    "type",
    "show_viewport",
    "show_render",
    "show_in_editmode",
    "show_on_cage",
    "show_expanded",
    "is_active",
    "use_pin_to_last",
    "use_apply_on_spline",
    # Geometry Nodes: UI states and bake configuration.
    "show_group_selector",
    "show_manage_panel",
    "bake_directory",
    "bake_target",
}

# Name of the temporary modifier used to read the real defaults.
_TEMP_NAME = "__etr_reset_defaults__"


def _is_resettable(prop):
    """True for the RNA properties of a modifier that count as parameters."""
    if prop.is_readonly or prop.identifier in EXCLUDED_PROPS:
        return False
    if prop.identifier.startswith("open_"):  # sub-panel open/closed states
        return False
    if prop.type in {'POINTER', 'COLLECTION'}:  # references are kept
        return False
    if getattr(prop, "subtype", None) == 'MATRIX':  # binding data (Hook)
        return False
    return True


def _rna_default(prop):
    """Return the RNA default of a property, handling arrays and enum flags."""
    if getattr(prop, "is_array", False):
        return tuple(prop.default_array)
    if prop.type == 'ENUM' and prop.is_enum_flag:
        return set(prop.default_flag)
    return prop.default


def _add_temp_modifier(obj, mod):
    """Add a fresh modifier of the same type to read its defaults, or None."""
    try:
        temp = obj.modifiers.new(name=_TEMP_NAME, type=mod.type)
    except (RuntimeError, TypeError):
        return None
    if temp is not None and mod.type == 'NODES':
        temp.node_group = mod.node_group
    return temp


def _reset_rna_properties(mod, temp):
    """Reset the modifier parameters. Return (reset_count, failed_count)."""
    reset = failed = 0
    for prop in mod.bl_rna.properties:
        if not _is_resettable(prop):
            continue
        name = prop.identifier
        try:
            value = getattr(temp, name) if temp is not None else _rna_default(prop)
            if getattr(mod, name) != value:
                setattr(mod, name, value)
                reset += 1
        except (AttributeError, TypeError, ValueError, RuntimeError):
            failed += 1
    return reset, failed


def _reset_geometry_nodes_inputs(mod, temp):
    """Reset the exposed inputs of a Geometry Nodes modifier.

    Blender 5.x exposes each input as mod.properties.inputs.<identifier>, a
    struct with "value", "type" (Value / Attribute...), "attribute_name", etc.
    Return (reset_count, failed_count).
    """
    reset = failed = 0
    if mod.type != 'NODES' or mod.node_group is None:
        return reset, failed

    inputs = mod.properties.inputs
    temp_inputs = temp.properties.inputs if temp is not None else None

    for item in mod.node_group.interface.items_tree:
        if item.item_type != 'SOCKET' or item.in_out != 'INPUT':
            continue
        current = getattr(inputs, item.identifier, None)
        if current is None:
            continue
        fresh = getattr(temp_inputs, item.identifier, None) if temp_inputs else None

        for prop in current.bl_rna.properties:
            name = prop.identifier
            if name in {"rna_type", "name"} or prop.is_readonly:
                continue
            try:
                if fresh is not None:
                    value = getattr(fresh, name)
                elif name == "value" and hasattr(item, "default_value"):
                    value = item.default_value
                elif name == "type":
                    has_attr = bool(getattr(item, "default_attribute_name", ""))
                    value = 'ATTRIBUTE' if has_attr else 'VALUE'
                elif name == "attribute_name":
                    value = getattr(item, "default_attribute_name", "")
                else:
                    continue
                if getattr(current, name) != value:
                    setattr(current, name, value)
                    reset += 1
            except (AttributeError, TypeError, ValueError, RuntimeError):
                failed += 1
    return reset, failed


def reset_modifier(obj, mod):
    """Reset `mod` (a modifier of `obj`) to its defaults.

    Return (reset_count, failed_count).
    """
    previous_active = obj.modifiers.active
    temp = _add_temp_modifier(obj, mod)
    try:
        reset_a, failed_a = _reset_rna_properties(mod, temp)
        reset_b, failed_b = _reset_geometry_nodes_inputs(mod, temp)
    finally:
        if temp is not None:
            obj.modifiers.remove(temp)
        # Adding a modifier makes it the active one: restore the original.
        obj.modifiers.active = previous_active
    obj.update_tag()
    return reset_a + reset_b, failed_a + failed_b


# ------------------------------------------------------------
# Operator
# ------------------------------------------------------------

class OBJECT_OT_reset_active_modifier(bpy.types.Operator):
    bl_idname = "object.reset_active_modifier_to_defaults"
    bl_label = "Reset Modifier to Defaults"
    bl_description = (
        "Reset all parameters of the modifier to their default values\n"
        "Does not affect visibility / render toggles"
    )
    bl_options = {'UNDO'}

    # Set by the right-click menu to reset a given modifier. Empty: the active
    # modifier of the active object.
    object_name: bpy.props.StringProperty(options={'HIDDEN', 'SKIP_SAVE'})
    modifier_name: bpy.props.StringProperty(options={'HIDDEN', 'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj is not None and len(obj.modifiers) > 0

    def execute(self, context):
        obj = bpy.data.objects.get(self.object_name) if self.object_name else context.object

        if not obj:
            self.report({'WARNING'}, "No active object")
            return {'CANCELLED'}

        if self.modifier_name:
            mod = obj.modifiers.get(self.modifier_name)
        else:
            mod = obj.modifiers.active
        if not mod:
            self.report({'WARNING'}, "No active modifier")
            return {'CANCELLED'}

        reset, failed = reset_modifier(obj, mod)

        message = f"'{mod.name}' reset to defaults ({reset} value(s) changed)"
        if failed:
            message += f", {failed} could not be reset"
            self.report({'WARNING'}, message)
        else:
            self.report({'INFO'}, message)
        return {'FINISHED'}


# ------------------------------------------------------------
# Panel (Sidebar (N) > Eterea Tools)
# ------------------------------------------------------------

class VIEW3D_PT_reset_active_modifier(bpy.types.Panel):
    bl_label = "Reset Modifier"
    bl_idname = "VIEW3D_PT_reset_active_modifier"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = eterea_ui.SIDEBAR_CATEGORY

    def draw(self, context):
        layout = self.layout
        obj = context.object

        if not obj:
            layout.label(text="No active object")
            return

        mod = obj.modifiers.active

        if not mod:
            layout.label(text="No active modifier")
            return

        box = layout.box()
        box.label(text="Active Modifier:", icon='MODIFIER')
        box.label(text=mod.name)

        if mod.type == 'NODES' and mod.node_group:
            box.label(text="Geometry Nodes", icon='NODETREE')

        layout.separator()
        layout.operator(
            OBJECT_OT_reset_active_modifier.bl_idname,
            icon='LOOP_BACK'
        )


# ------------------------------------------------------------
# Right-click menu on any modifier parameter
# ------------------------------------------------------------

# Matches the start of a data path such as 'modifiers["Array"].count' or
# 'modifiers["GeometryNodes"].properties.inputs.Socket_2.value'.
_MODIFIER_PATH = re.compile(r'^modifiers\["((?:[^"\\]|\\.)*)"\]')


def modifier_from_pointer(pointer):
    """Return (object, modifier) for a right-clicked button, or (None, None).

    `pointer` is context.button_pointer: the modifier itself, or a struct that
    belongs to one (e.g. a Geometry Nodes input).
    """
    if pointer is None:
        return None, None
    obj = getattr(pointer, "id_data", None)
    if not isinstance(obj, bpy.types.Object):
        return None, None
    if isinstance(pointer, bpy.types.Modifier):
        return obj, pointer
    try:
        path = pointer.path_from_id()
    except (ValueError, TypeError):
        return None, None
    match = _MODIFIER_PATH.match(path)
    if match is None:
        return None, None
    name = match.group(1).replace('\\"', '"').replace('\\\\', '\\')
    return obj, obj.modifiers.get(name)


def draw_button_context_menu(self, context):
    obj, mod = modifier_from_pointer(getattr(context, "button_pointer", None))
    if mod is None:
        return
    layout = self.layout
    layout.separator()
    op = layout.operator(
        OBJECT_OT_reset_active_modifier.bl_idname,
        text="Reset Modifier to Defaults",
        icon='LOOP_BACK',
    )
    op.object_name = obj.name
    op.modifier_name = mod.name


# ------------------------------------------------------------
# Registration
# ------------------------------------------------------------

classes = (
    OBJECT_OT_reset_active_modifier,
    VIEW3D_PT_reset_active_modifier,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.UI_MT_button_context_menu.append(draw_button_context_menu)


def unregister():
    bpy.types.UI_MT_button_context_menu.remove(draw_button_context_menu)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
