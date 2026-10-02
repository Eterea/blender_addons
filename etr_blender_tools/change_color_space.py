# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Cristobal Vila (etereaestudios.com)

"""
Change Color Space

Adds two commands (to Non-Color / to sRGB) to the shared "Eterea Tools"
submenu of the Shader Editor right-click menu (see eterea_ui.py). Only selected
Image Texture nodes that actually hold an image are affected. Note that the
Color Space belongs to the image datablock, so every node using that same
image is affected too.
"""

bl_info = {
    "name": "Change Color Space",
    "author": "Idea by Cristobal Vila / Code by Claude.ai",
    "version": (1, 2, 3),
    "blender": (5, 2, 0),
    "location": "Shader Editor > Right-Click > Eterea Tools",
    "description": (
        "Quickly switch the Color Space of the images used by the selected "
        "Image Texture nodes (Non-Color or sRGB)."
    ),
    "category": "Node",
}

import bpy

from . import eterea_ui


# ------------------------------------------------------------------------
# Base logic (not registered as an operator)
# ------------------------------------------------------------------------
def change_color_space(context, target_space):
    """Set `target_space` on the images of the selected Image Texture nodes.

    Return the number of images changed, or None if `target_space` does not
    exist in the current OCIO configuration (e.g. a custom ACES config).
    """
    # context.selected_nodes refers to the tree being edited, so this also
    # works inside node groups (space_data.node_tree is always the root tree).
    count = 0

    for node in context.selected_nodes or ():
        if node.type == 'TEX_IMAGE' and node.image is not None:
            if node.image.colorspace_settings.name != target_space:
                try:
                    node.image.colorspace_settings.name = target_space
                except TypeError:
                    return None
                count += 1

    return count


def _report_result(operator, count, target_space):
    if count is None:
        operator.report(
            {'ERROR'},
            f"Color space \"{target_space}\" is not available in the current "
            "OCIO configuration",
        )
        return {'CANCELLED'}
    operator.report({'INFO'}, f"Changed {count} texture(s) to {target_space}")
    return {'FINISHED'}


# ------------------------------------------------------------------------
# Operators (one per target color space, sharing the same logic)
# ------------------------------------------------------------------------
class _ColorSpaceOperatorMixin:
    bl_options = {'REGISTER', 'UNDO'}
    target_space = ""

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space is not None and space.type == 'NODE_EDITOR' and space.edit_tree is not None

    def execute(self, context):
        count = change_color_space(context, self.target_space)
        return _report_result(self, count, self.target_space)


class NODE_OT_color_space_to_non_color(_ColorSpaceOperatorMixin, bpy.types.Operator):
    """Set Color Space to Non-Color for selected Image Texture nodes"""
    bl_idname = "node.color_space_to_non_color"
    bl_label = "Color Space to Non-Color"
    target_space = "Non-Color"


class NODE_OT_color_space_to_srgb(_ColorSpaceOperatorMixin, bpy.types.Operator):
    """Set Color Space to sRGB for selected Image Texture nodes"""
    bl_idname = "node.color_space_to_srgb"
    bl_label = "Color Space to sRGB"
    target_space = "sRGB"


# ------------------------------------------------------------------------
# "Eterea Tools" submenu section (see eterea_ui.py)
# ------------------------------------------------------------------------
def poll_eterea_tools_section(context):
    """Only show the items in the Shader Editor."""
    space = context.space_data
    return (
        space is not None
        and space.type == 'NODE_EDITOR'
        and space.tree_type == 'ShaderNodeTree'
        and space.edit_tree is not None
    )


def draw_eterea_tools_section(layout, context):
    layout.operator(NODE_OT_color_space_to_non_color.bl_idname, icon='IMAGE_DATA')
    layout.operator(NODE_OT_color_space_to_srgb.bl_idname, icon='IMAGE_DATA')


# ------------------------------------------------------------------------
# Registration
# ------------------------------------------------------------------------
classes = (
    NODE_OT_color_space_to_non_color,
    NODE_OT_color_space_to_srgb,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    eterea_ui.add_section(
        eterea_ui.NODE_CONTEXT,
        __name__,
        draw_eterea_tools_section,
        poll_eterea_tools_section,
    )


def unregister():
    eterea_ui.remove_section(eterea_ui.NODE_CONTEXT, __name__)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
