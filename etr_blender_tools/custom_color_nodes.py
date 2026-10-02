# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Cristobal Vila (etereaestudios.com)

"""
Custom Color Nodes

Quickly set the background color of the selected nodes and frames in any node
editor (Geometry Nodes, Shader, Compositor, Texture).

* Panel "Custom Colors Palette" in the Node Editor Sidebar (N) > Node tab, and
  a floating version of the same palette (default key: D, configurable in the
  add-on Preferences).
* The palette has two rows of 10 color swatches:
    - Row 1: 10 vibrant colors, freely editable in the Preferences.
    - Row 2: 10 darkened colors, derived automatically from row 1 by two
      shared factors (Saturation and Value), also set in the Preferences.
  Each color has a user-editable name, shown in the tooltip of its swatch
  ("Dark <name>" for the darkened row).
* "Color" is a live color picker: it sets any color on the selected nodes.
* "Copy from Active" copies the color of the active node to the selected ones.
* "Disable" turns the custom color off on the selected nodes.

The colors and their names live in the add-on Preferences (section "Custom
Color Nodes"), so they persist between sessions. "Reset Values" restores the
defaults below.
"""

bl_info = {
    "name": "Custom Color Nodes",
    "author": "Idea by Cristobal Vila / Code by Claude.ai",
    "version": (2, 1, 1),
    "blender": (5, 2, 0),
    "location": "Node Editor > Sidebar (N) > Node > Custom Colors Palette",
    "description": (
        "Customizable 10+10 color palette to quickly set the background color "
        "of the selected nodes and frames in any node editor."
    ),
    "category": "Node",
}

import colorsys

import bpy
import bpy.utils.previews
from bpy.props import (
    BoolProperty,
    FloatProperty,
    FloatVectorProperty,
    IntProperty,
    StringProperty,
)

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

NUM_COLORS = 10

# Default vibrant colors (the "light" set of the original add-on). They are
# also the values restored by "Reset Values".
DEFAULT_COLORS = (
    (0.500, 0.500, 0.500),  # Color 1  (Grey)
    (0.750, 0.250, 0.250),  # Color 2  (Red)
    (0.700, 0.400, 0.100),  # Color 3  (Orange)
    (0.650, 0.550, 0.200),  # Color 4  (Yellow)
    (0.400, 0.600, 0.100),  # Color 5  (Lime)
    (0.100, 0.600, 0.200),  # Color 6  (Green)
    (0.100, 0.600, 0.700),  # Color 7  (Cyan)
    (0.200, 0.400, 0.900),  # Color 8  (Blue)
    (0.350, 0.200, 0.750),  # Color 9  (Purple)
    (0.650, 0.200, 0.600),  # Color 10 (Magenta)
)

# Default names of the vibrant colors (editable in the Preferences). They are
# also the names restored by "Reset Values".
DEFAULT_NAMES = (
    "Grey",
    "Red",
    "Orange",
    "Yellow",
    "Lime",
    "Green",
    "Cyan",
    "Blue",
    "Purple",
    "Magenta",
)

# Prefix added to a color name to name its darkened version.
DARKENED_PREFIX = "Dark "

# Default factors used to derive the darkened colors: the Saturation and Value
# of each vibrant color are multiplied by these numbers.
DEFAULT_SATURATION = 0.90
DEFAULT_VALUE = 0.42

KEYMAP_NAME = "Node Editor"
DEFAULT_KEY = 'D'
POPUP_ID = "ETEREA_PT_custom_colors_popup"

# Default vertical offset (in pixels, positive = up) of the floating palette
# relative to the mouse pointer, so it does not cover the nodes being colored.
DEFAULT_POPUP_OFFSET = 100

# --------------------------------------------------------------------------
# Color helpers
# --------------------------------------------------------------------------


def derive_color(rgb, saturation_factor, value_factor):
    """Return rgb with its HSV saturation and value scaled by the factors."""
    h, s, v = colorsys.rgb_to_hsv(*rgb)
    s = min(max(s * saturation_factor, 0.0), 1.0)
    v = min(max(v * value_factor, 0.0), 1.0)
    return colorsys.hsv_to_rgb(h, s, v)


def get_settings(context=None):
    """Return this tool's settings from the add-on Preferences, or None."""
    # Imported here: preferences.py imports this module at load time.
    from . import preferences

    prefs = preferences.get_preferences(context)
    return getattr(prefs, "custom_color_nodes", None)


def get_palette(settings):
    """Return (vibrant, darkened): two lists of NUM_COLORS RGB tuples.

    Falls back to the built-in defaults if the Preferences are unavailable, so
    the palette keeps working in any case.
    """
    if settings is None:
        vibrant = [tuple(c) for c in DEFAULT_COLORS]
        saturation, value = DEFAULT_SATURATION, DEFAULT_VALUE
    else:
        vibrant = [
            tuple(getattr(settings, f"color_{i}")) for i in range(1, NUM_COLORS + 1)
        ]
        saturation, value = settings.saturation, settings.value
    darkened = [derive_color(c, saturation, value) for c in vibrant]
    return vibrant, darkened


def get_names(settings):
    """Return (vibrant_names, darkened_names): two lists of NUM_COLORS strings.

    An empty name falls back to its default, so a tooltip is never blank.
    """
    vibrant = []
    for i in range(1, NUM_COLORS + 1):
        name = getattr(settings, f"name_{i}", "").strip() if settings else ""
        vibrant.append(name or DEFAULT_NAMES[i - 1])
    return vibrant, [DARKENED_PREFIX + name for name in vibrant]


def _redraw_all(self, context):
    """Update callback: refresh every area so palettes show the new colors."""
    wm = (context or bpy.context).window_manager
    if wm is None:
        return
    for window in wm.windows:
        for area in window.screen.areas:
            area.tag_redraw()


# --------------------------------------------------------------------------
# Preferences data (registered by preferences.py, which owns the single
# AddonPreferences class of the kit)
# --------------------------------------------------------------------------


def _apply_picker_color(self, context):
    """Update callback of the live picker: color the selected nodes."""
    for node in getattr(context, "selected_nodes", None) or ():
        node.use_custom_color = True
        node.color = self.custom_color
    _redraw_all(self, context)


def _color_prop(index):
    return FloatVectorProperty(
        name=f"Color {index}",
        description=f"Vibrant color {index} of the palette",
        subtype='COLOR_GAMMA',  # the value shown is the value stored in node.color
        size=3,
        min=0.0,
        max=1.0,
        default=DEFAULT_COLORS[index - 1],
        update=_redraw_all,
    )


def _name_prop(index):
    return StringProperty(
        name=f"Name {index}",
        description=f"Name of color {index}, shown in the tooltip of its swatches",
        default=DEFAULT_NAMES[index - 1],
    )


def _derived_prop(index):
    """Read-only color: the darkened version of vibrant color `index`.

    It has a getter and no setter, so it is computed on the fly from the
    vibrant color and the two shared factors, is never stored, and cannot be
    edited directly. It exists only to show the swatch in the Preferences.
    """

    def get(self):
        return derive_color(
            tuple(getattr(self, f"color_{index}")), self.saturation, self.value
        )

    return FloatVectorProperty(
        name=f"Color {index} (darkened)",
        description=(
            f"Darkened color {index}, derived from the vibrant color with the "
            "shared Saturation and Value factors"
        ),
        subtype='COLOR_GAMMA',
        size=3,
        min=0.0,
        max=1.0,
        get=get,
    )


class CustomColorNodesSettings(bpy.types.PropertyGroup):
    color_1: _color_prop(1)
    color_2: _color_prop(2)
    color_3: _color_prop(3)
    color_4: _color_prop(4)
    color_5: _color_prop(5)
    color_6: _color_prop(6)
    color_7: _color_prop(7)
    color_8: _color_prop(8)
    color_9: _color_prop(9)
    color_10: _color_prop(10)

    name_1: _name_prop(1)
    name_2: _name_prop(2)
    name_3: _name_prop(3)
    name_4: _name_prop(4)
    name_5: _name_prop(5)
    name_6: _name_prop(6)
    name_7: _name_prop(7)
    name_8: _name_prop(8)
    name_9: _name_prop(9)
    name_10: _name_prop(10)

    derived_1: _derived_prop(1)
    derived_2: _derived_prop(2)
    derived_3: _derived_prop(3)
    derived_4: _derived_prop(4)
    derived_5: _derived_prop(5)
    derived_6: _derived_prop(6)
    derived_7: _derived_prop(7)
    derived_8: _derived_prop(8)
    derived_9: _derived_prop(9)
    derived_10: _derived_prop(10)

    custom_color: FloatVectorProperty(
        name="Color",
        description=(
            "Live color picker: any change is applied right away to the "
            "selected nodes and frames"
        ),
        subtype='COLOR_GAMMA',
        size=3,
        min=0.0,
        max=1.0,
        default=DEFAULT_COLORS[7],
        update=_apply_picker_color,
    )

    popup_offset_y: IntProperty(
        name="Vertical Offset",
        description=(
            "Vertical offset of the floating palette relative to the mouse "
            "pointer. Positive values move it up, negative values move it "
            "down"
        ),
        subtype='PIXEL',
        min=-1000,
        max=1000,
        soft_min=-300,
        soft_max=300,
        default=DEFAULT_POPUP_OFFSET,
    )

    saturation: FloatProperty(
        name="Saturation",
        description=(
            "Saturation of the darkened colors, as a fraction of the "
            "saturation of their vibrant color (shared by all 10)"
        ),
        subtype='FACTOR',
        min=0.0,
        max=1.0,
        default=DEFAULT_SATURATION,
        update=_redraw_all,
    )
    value: FloatProperty(
        name="Value",
        description=(
            "Value (brightness) of the darkened colors, as a fraction of the "
            "value of their vibrant color (shared by all 10)"
        ),
        subtype='FACTOR',
        min=0.0,
        max=1.0,
        default=DEFAULT_VALUE,
        update=_redraw_all,
    )


# --------------------------------------------------------------------------
# Swatch icons
#
# Blender cannot tint an operator button with an arbitrary color, so each
# palette button shows a small generated icon: a square filled with the color.
# --------------------------------------------------------------------------

_ICON_SIZE = 32
_icons = None       # bpy.utils.previews collection
_icons_key = None   # colors the cached icons were built for


def _sync_icons(vibrant, darkened):
    """Drop the cached icons if the palette colors changed."""
    global _icons_key
    key = (tuple(vibrant), tuple(darkened))
    if key != _icons_key:
        _icons.clear()
        _icons_key = key


def _get_icon_id(name, rgb):
    """Return the icon id for a swatch, generating it on first use."""
    preview = _icons.get(name)
    if preview is None:
        preview = _icons.new(name)
        preview.icon_size = (_ICON_SIZE, _ICON_SIZE)
        preview.icon_pixels_float = [*rgb, 1.0] * (_ICON_SIZE * _ICON_SIZE)
    return preview.icon_id


# --------------------------------------------------------------------------
# Operators
# --------------------------------------------------------------------------


def _in_node_editor(context):
    space = context.space_data
    return space is not None and space.type == 'NODE_EDITOR'


class NODE_OT_set_custom_color(bpy.types.Operator):
    bl_idname = "node.set_custom_color"
    bl_label = "Set Custom Color to Selected Nodes and Frames"
    bl_description = "Set the color of the selected nodes and frames"
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty(
        name="Color",
        description="Palette color number (1 to 10)",
        min=1,
        max=NUM_COLORS,
        default=1,
    )
    darkened: BoolProperty(
        name="Darkened",
        description="Use the darkened version of the color",
        default=False,
    )

    @classmethod
    def poll(cls, context):
        return _in_node_editor(context)

    @classmethod
    def description(cls, context, properties):
        # Only the color name: it is the second line of the tooltip.
        vibrant, darkened = get_names(get_settings(context))
        names = darkened if properties.darkened else vibrant
        return names[properties.index - 1]

    def execute(self, context):
        nodes = context.selected_nodes
        if not nodes:
            self.report({'WARNING'}, "No nodes selected")
            return {'CANCELLED'}

        vibrant, darkened = get_palette(get_settings(context))
        palette = darkened if self.darkened else vibrant
        color = palette[self.index - 1]

        for node in nodes:
            node.use_custom_color = True
            node.color = color
        return {'FINISHED'}


class NODE_OT_disable_custom_colors(bpy.types.Operator):
    bl_idname = "node.disable_custom_colors"
    bl_label = "Disable Custom Colors"
    bl_description = "Disable the custom color of the selected nodes and frames"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _in_node_editor(context)

    def execute(self, context):
        nodes = context.selected_nodes
        if not nodes:
            self.report({'WARNING'}, "No nodes selected")
            return {'CANCELLED'}
        for node in nodes:
            node.use_custom_color = False
        return {'FINISHED'}


class NODE_OT_copy_color_from_active(bpy.types.Operator):
    bl_idname = "node.copy_color_from_active"
    bl_label = "Copy from Active"
    bl_description = (
        "Copy the color of the active node or frame to all the selected "
        "nodes and frames"
    )
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _in_node_editor(context) and context.active_node is not None

    def execute(self, context):
        active = context.active_node
        others = [node for node in context.selected_nodes if node != active]
        if not others:
            self.report({'WARNING'}, "No other nodes selected")
            return {'CANCELLED'}
        for node in others:
            node.use_custom_color = active.use_custom_color
            node.color = active.color
        return {'FINISHED'}


class NODE_OT_custom_colors_reset(bpy.types.Operator):
    bl_idname = "node.custom_colors_reset"
    bl_label = "Reset Values"
    bl_description = (
        "Restore the original 10 colors and their names, the default "
        "Saturation and Value of the darkened colors, and the default "
        "Vertical Offset of the floating palette"
    )
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return get_settings(context) is not None

    def execute(self, context):
        settings = get_settings(context)
        for i in range(1, NUM_COLORS + 1):
            settings.property_unset(f"color_{i}")
            settings.property_unset(f"name_{i}")
        settings.property_unset("saturation")
        settings.property_unset("value")
        settings.property_unset("popup_offset_y")
        _redraw_all(None, context)
        return {'FINISHED'}


class NODE_OT_call_custom_colors_palette(bpy.types.Operator):
    bl_idname = "node.call_custom_colors_palette"
    bl_label = "Custom Colors Palette"
    bl_description = "Open the floating Custom Colors palette above the mouse pointer"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return _in_node_editor(context)

    def invoke(self, context, event):
        # The popup stays open after picking a color (keep_open=True), so
        # several colors can be tried in a row; it closes when the mouse
        # leaves it.
        #
        # Popups open centered on the mouse pointer, which would cover a small
        # node. To show the palette above it, the pointer is moved up by the
        # offset from the Preferences just before opening the popup.
        settings = get_settings(context)
        offset = settings.popup_offset_y if settings else DEFAULT_POPUP_OFFSET
        offset_px = int(offset * context.preferences.system.pixel_size)
        window = context.window
        if offset_px and window is not None:
            try:
                window.cursor_warp(event.mouse_x, event.mouse_y + offset_px)
            except Exception:
                pass  # not critical: the palette then opens at the pointer
        bpy.ops.wm.call_panel('INVOKE_DEFAULT', name=POPUP_ID, keep_open=True)
        return {'FINISHED'}


# --------------------------------------------------------------------------
# Palette UI
# --------------------------------------------------------------------------


def draw_palette(layout, context):
    """Draw the two rows of swatches, the live picker and the two buttons.

    Each row is a split layout with 10 equal columns, so the buttons stretch
    to the full width of the panel. (The color square inside each button keeps
    its fixed icon size.)
    """
    settings = get_settings(context)
    vibrant, darkened = get_palette(settings)
    use_icons = _icons is not None
    if use_icons:
        _sync_icons(vibrant, darkened)

    col = layout.column(align=True)
    for is_darkened, colors in ((False, vibrant), (True, darkened)):
        row = col.split(factor=1.0 / NUM_COLORS, align=True)
        for number, rgb in enumerate(colors, start=1):
            if use_icons:
                name = f"{'d' if is_darkened else 'v'}{number}"
                op = row.operator(
                    NODE_OT_set_custom_color.bl_idname,
                    text="",
                    icon_value=_get_icon_id(name, rgb),
                )
            else:
                op = row.operator(NODE_OT_set_custom_color.bl_idname, text=str(number))
            op.index = number
            op.darkened = is_darkened

    layout.separator()
    if settings is not None:
        split = layout.split(factor=0.34)
        split.prop(settings, "custom_color", text="")
        buttons = split.row()
    else:
        buttons = layout.row()
    buttons.operator(NODE_OT_copy_color_from_active.bl_idname, text="Copy")
    buttons.operator(NODE_OT_disable_custom_colors.bl_idname, text="Disable")


class NODE_PT_custom_colors_palette(bpy.types.Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Node"
    bl_label = "Custom Colors Palette"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space is not None and getattr(space, "edit_tree", None) is not None

    def draw(self, context):
        draw_palette(self.layout, context)


class ETEREA_PT_custom_colors_popup(bpy.types.Panel):
    """Floating version of the palette, opened with a key in the node editors."""

    # Popover-only panel: it never shows in a region, it is only called with
    # wm.call_panel (same technique as Blender's own TOPBAR_PT_name).
    bl_space_type = 'TOPBAR'  # dummy
    bl_region_type = 'HEADER'
    bl_idname = POPUP_ID
    bl_label = "Custom Colors Palette"
    bl_ui_units_x = 13

    def draw(self, context):
        draw_palette(self.layout, context)


# --------------------------------------------------------------------------
# Preferences UI (section of the kit Preferences, see preferences.py)
# --------------------------------------------------------------------------


def _find_user_keymap_item(context):
    """Return (keyconfig, keymap, item) of the floating-palette shortcut."""
    kc = context.window_manager.keyconfigs.user
    km = kc.keymaps.get(KEYMAP_NAME) if kc is not None else None
    if km is not None:
        for kmi in km.keymap_items:
            if kmi.idname == NODE_OT_call_custom_colors_palette.bl_idname:
                return kc, km, kmi
    return None, None, None


# Fixed widths (in UI units, so they follow the UI scale) of the Preferences
# layout: label column, color bars and shared sliders.
_PREFS_LABEL_UNITS = 5
_PREFS_BAR_UNITS = 4
_PREFS_SLIDER_UNITS = 10


def _cell(row, units):
    """Return a sub-layout of a fixed width inside `row`."""
    cell = row.row(align=True)
    cell.ui_units_x = units
    return cell


def draw_preferences(layout, context):
    settings = get_settings(context)
    if settings is None:
        layout.label(text="Preferences not available.", icon='ERROR')
        return

    col = layout.column(align=True)
    row = col.row()
    row.alignment = 'LEFT'
    _cell(row, _PREFS_LABEL_UNITS).label(text="Name")
    _cell(row, _PREFS_BAR_UNITS).label(text="Vibrant")
    _cell(row, _PREFS_BAR_UNITS).label(text="Darkened")

    for number in range(1, NUM_COLORS + 1):
        row = col.row()
        row.alignment = 'LEFT'
        _cell(row, _PREFS_LABEL_UNITS).prop(settings, f"name_{number}", text="")
        _cell(row, _PREFS_BAR_UNITS).prop(settings, f"color_{number}", text="")
        _cell(row, _PREFS_BAR_UNITS).prop(settings, f"derived_{number}", text="")

    layout.label(text="Names and vibrant colors are editable. Darkened colors are derived from them.")

    layout.separator()
    layout.label(text="Darkened colors (shared by all 10):")
    row = layout.row()
    row.alignment = 'LEFT'
    sliders = row.column(align=True)
    sliders.ui_units_x = _PREFS_SLIDER_UNITS
    sliders.prop(settings, "saturation")
    sliders.prop(settings, "value")

    layout.separator()
    layout.label(text="Floating palette (Node Editors):")
    row = layout.row()
    row.alignment = 'LEFT'
    col = row.column(align=True)
    col.ui_units_x = _PREFS_SLIDER_UNITS
    col.prop(settings, "popup_offset_y")
    col.separator()
    col.operator(NODE_OT_custom_colors_reset.bl_idname, icon='LOOP_BACK')

    layout.separator()
    layout.label(text="Shortcut:")
    kc, km, kmi = _find_user_keymap_item(context)
    if kmi is None:
        layout.label(text="Shortcut not available.", icon='INFO')
        return
    try:
        import rna_keymap_ui

        rna_keymap_ui.draw_kmi([], kc, km, kmi, layout, 0)
    except Exception:
        # The stock keymap widget failed: fall back to a plain key field.
        layout.prop(kmi, "type", text="Key")


# --------------------------------------------------------------------------
# Registration
# --------------------------------------------------------------------------

classes = (
    NODE_OT_set_custom_color,
    NODE_OT_disable_custom_colors,
    NODE_OT_copy_color_from_active,
    NODE_OT_custom_colors_reset,
    NODE_OT_call_custom_colors_palette,
    NODE_PT_custom_colors_palette,
    ETEREA_PT_custom_colors_popup,
)

_keymap_items = []


def _register_keymap():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon if wm is not None else None
    if kc is None:  # background mode: no keyconfig
        return
    km = kc.keymaps.new(name=KEYMAP_NAME, space_type='NODE_EDITOR')
    kmi = km.keymap_items.new(
        NODE_OT_call_custom_colors_palette.bl_idname, type=DEFAULT_KEY, value='PRESS'
    )
    _keymap_items.append((km, kmi))


def _unregister_keymap():
    for km, kmi in _keymap_items:
        try:
            km.keymap_items.remove(kmi)
        except (RuntimeError, ReferenceError):
            pass
    _keymap_items.clear()


def register():
    global _icons, _icons_key
    from . import preferences

    _icons = bpy.utils.previews.new()
    _icons_key = None
    for cls in classes:
        bpy.utils.register_class(cls)
    _register_keymap()
    preferences.add_section("custom_color_nodes", "Custom Color Nodes", draw_preferences)


def unregister():
    global _icons, _icons_key
    from . import preferences

    preferences.remove_section("custom_color_nodes")
    _unregister_keymap()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    if _icons is not None:
        bpy.utils.previews.remove(_icons)
    _icons = None
    _icons_key = None
