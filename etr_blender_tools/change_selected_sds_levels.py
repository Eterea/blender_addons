# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Cristobal Vila (etereaestudios.com)

"""
Change Selected SDS Levels

Sub-panel "Levels" with two integer fields (stored on the Scene as
sds_levels_viewport / sds_levels_render) and an "Apply New Levels" button that
writes them into every Subdivision Surface modifier of the selected objects.

This module also defines the shared "Subdivision" panel of the Eterea Tools
Sidebar tab. Its three sub-panels come from three tools:
  - Levels     (this module)
  - UV Smooth  (change_selected_sds_uv_smooth.py)
  - Remove     (remove_subdivision_modifiers.py)
This module is registered before the other two (MODULES in __init__.py is in
alphabetical order), so the parent panel always exists before its children.
"""

bl_info = {
    "name": "Change Selected SDS Levels",
    "author": "Idea by Cristobal Vila / Code by Claude.ai",
    "version": (1, 1, 0),
    "blender": (5, 2, 0),
    "location": "3D Viewport > Sidebar (N) > Eterea Tools > Subdivision > Levels",
    "description": (
        "Set the Viewport and Render levels of every Subdivision Surface "
        "modifier on the selected objects."
    ),
    "category": "Object",
}

import bpy

from . import eterea_ui

# Identifier of the shared "Subdivision" panel (parent of the three
# Subdivision sub-panels, see the module docstring).
SUBDIVISION_PANEL_ID = "ETR_PT_subdivision"


class ETR_PT_subdivision(bpy.types.Panel):
    """Shared parent panel of the Subdivision tools (it has no content of its own)"""
    bl_label = "Subdivision"
    bl_idname = SUBDIVISION_PANEL_ID
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = eterea_ui.SIDEBAR_CATEGORY

    def draw(self, context):
        pass


class OBJECT_PT_apply_sds_levels(bpy.types.Panel):
    # The identifier is kept from the former stand-alone panel.
    bl_label = "Levels"
    bl_idname = "OBJECT_PT_apply_sds_levels"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = eterea_ui.SIDEBAR_CATEGORY
    bl_parent_id = SUBDIVISION_PANEL_ID

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Integer fields for viewport and render levels
        layout.prop(scene, "sds_levels_viewport", text="Levels Viewport")
        layout.prop(scene, "sds_levels_render", text="Levels Render")

        # Apply New Levels button
        layout.operator("object.apply_new_sds_levels", text="Apply New Levels")


class OBJECT_OT_apply_new_sds_levels(bpy.types.Operator):
    bl_label = "Apply New SDS Levels"
    bl_idname = "object.apply_new_sds_levels"
    bl_description = "Apply new subdivision levels to all selected objects with subdivision modifiers"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects)

    def execute(self, context):
        # Retrieve user-defined viewport and render levels
        viewport_level = context.scene.sds_levels_viewport
        render_level = context.scene.sds_levels_render

        # Apply levels to all selected objects with a Subdivision Surface modifier
        count = 0
        for obj in context.selected_objects:
            for mod in obj.modifiers:
                if mod.type == 'SUBSURF':
                    mod.levels = viewport_level
                    mod.render_levels = render_level
                    count += 1

        if count == 0:
            self.report({'WARNING'}, "No Subdivision modifiers found on the selected objects")
            return {'CANCELLED'}

        noun = "modifier" if count == 1 else "modifiers"
        self.report(
            {'INFO'},
            f"Levels {viewport_level} / {render_level} applied to {count} Subdivision {noun}",
        )
        return {'FINISHED'}


classes = (
    ETR_PT_subdivision,
    OBJECT_PT_apply_sds_levels,
    OBJECT_OT_apply_new_sds_levels,
)


def register():
    # Scene properties (their names are kept: values saved in .blend files
    # depend on them)
    bpy.types.Scene.sds_levels_viewport = bpy.props.IntProperty(
        name="Levels Viewport",
        default=1,
        min=0,
        max=6,
        description="Subdivision level for viewport"
    )
    bpy.types.Scene.sds_levels_render = bpy.props.IntProperty(
        name="Levels Render",
        default=3,
        min=0,
        max=6,
        description="Subdivision level for render"
    )

    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.sds_levels_viewport
    del bpy.types.Scene.sds_levels_render
