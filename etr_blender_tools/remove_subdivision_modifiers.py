# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Cristobal Vila (etereaestudios.com)

"""
Remove Subdivision Modifiers

Sub-panel "Remove" (inside the shared "Subdivision" panel, defined in
change_selected_sds_levels.py) with a single button that deletes all
Subdivision Surface modifiers found on the selected objects.
"""

bl_info = {
    "name": "Remove Subdivision Modifiers",
    "author": "Idea by Cristobal Vila / Code by Claude.ai",
    "version": (1, 1, 0),
    "blender": (5, 2, 0),
    "location": "3D Viewport > Sidebar (N) > Eterea Tools > Subdivision > Remove",
    "description": "Remove every Subdivision Surface modifier from the selected objects.",
    "category": "Object",
}

import bpy

from . import eterea_ui
from .change_selected_sds_levels import SUBDIVISION_PANEL_ID


class OBJECT_OT_remove_subdivision_modifiers(bpy.types.Operator):
    """Remove Subdivision Modifiers from Selected Objects"""
    bl_idname = "object.remove_subdivision_modifiers"
    bl_label = "Remove Subdivision Modifiers"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects)

    def execute(self, context):
        count = 0
        for obj in context.selected_objects:
            # Collect first, then remove: clearer, and it does not rely on how
            # the collection behaves when it changes while being iterated.
            for mod in [m for m in obj.modifiers if m.type == 'SUBSURF']:
                obj.modifiers.remove(mod)
                count += 1

        noun = "modifier" if count == 1 else "modifiers"
        self.report({'INFO'}, f"Removed {count} Subdivision {noun}")
        return {'FINISHED'}


class OBJECT_PT_remove_subdivision_panel(bpy.types.Panel):
    """Sub-panel of the shared Subdivision panel (Eterea Tools Sidebar tab)"""
    # The identifier is kept from the former stand-alone panel.
    bl_label = "Remove"
    bl_idname = "OBJECT_PT_remove_subdivision_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = eterea_ui.SIDEBAR_CATEGORY
    bl_parent_id = SUBDIVISION_PANEL_ID

    def draw(self, context):
        layout = self.layout
        layout.operator("object.remove_subdivision_modifiers")


classes = (
    OBJECT_OT_remove_subdivision_modifiers,
    OBJECT_PT_remove_subdivision_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
