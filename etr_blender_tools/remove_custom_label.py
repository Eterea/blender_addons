# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Cristobal Vila (etereaestudios.com)

"""
Remove Custom Label from Selected Nodes

Clears the Custom Label of every selected node (and frame). Nodes that have no
Custom Label are left untouched. Works in every Node Editor: Shader, Geometry
Nodes, Compositor and Texture.

The command lives in the shared "Eterea Tools" submenu of the Node Editor
right-click menu (see eterea_ui.py).
"""

bl_info = {
    "name": "Remove Custom Label from Selected Nodes",
    "author": "Idea by Cristobal Vila / Code by Claude.ai",
    "version": (1, 0, 0),
    "blender": (5, 2, 0),
    "location": "Node Editors > Right-Click > Eterea Tools",
    "description": (
        "Remove the Custom Label of the selected nodes in the Shader, "
        "Geometry Nodes, Compositor and Texture editors."
    ),
    "category": "Node",
}

import bpy

from . import eterea_ui


def _node_editor_has_tree(context):
    space = context.space_data
    return (
        space is not None
        and space.type == 'NODE_EDITOR'
        and space.edit_tree is not None
    )


class NODE_OT_etr_remove_custom_label(bpy.types.Operator):
    """Remove the Custom Label of the selected nodes"""
    bl_idname = "node.etr_remove_custom_label"
    bl_label = "Remove Custom Label from Selected Nodes"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _node_editor_has_tree(context)

    def execute(self, context):
        count = 0

        for node in context.selected_nodes:
            # Nodes without a Custom Label (empty string) are skipped.
            if node.label:
                node.label = ""
                count += 1

        if count:
            self.report(
                {'INFO'},
                f"Custom Label removed from {count} node{'s' if count != 1 else ''}"
            )
        else:
            self.report({'INFO'}, "No selected node had a Custom Label")
        return {'FINISHED'}


# -----------------------------------------------------------------------------
# "Eterea Tools" submenu section (see eterea_ui.py)
# -----------------------------------------------------------------------------

def poll_eterea_tools_section(context):
    return _node_editor_has_tree(context)


def draw_eterea_tools_section(layout, context):
    layout.operator(
        NODE_OT_etr_remove_custom_label.bl_idname,
        text="Remove Custom Label from Selected Nodes",
        icon='X',
    )


def register():
    bpy.utils.register_class(NODE_OT_etr_remove_custom_label)
    eterea_ui.add_section(
        eterea_ui.NODE_CONTEXT,
        __name__,
        draw_eterea_tools_section,
        poll_eterea_tools_section,
    )


def unregister():
    eterea_ui.remove_section(eterea_ui.NODE_CONTEXT, __name__)
    bpy.utils.unregister_class(NODE_OT_etr_remove_custom_label)
