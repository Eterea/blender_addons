# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Cristobal Vila (etereaestudios.com)

"""
Change SDS UV Smooth

Sub-panel "UV Smooth" (inside the shared "Subdivision" panel, defined in
change_selected_sds_levels.py) with two buttons (Keep Boundaries / Keep Corners)
that set the UV Smooth option of every Subdivision Surface modifier found on
the selected objects.
"""

bl_info = {
    "name": "Change SDS UV Smooth",
    "author": "Idea by Cristobal Vila / Code by Claude.ai",
    "version": (1, 1, 0),
    "blender": (5, 2, 0),
    "location": "3D Viewport > Sidebar (N) > Eterea Tools > Subdivision > UV Smooth",
    "description": (
        "Switch the UV Smooth mode (Keep Boundaries / Keep Corners) of every "
        "Subdivision Surface modifier on the selected objects."
    ),
    "category": "Object",
}

import bpy

from . import eterea_ui
from .change_selected_sds_levels import SUBDIVISION_PANEL_ID


# -----------------------------------------------------------------------------
# Panel
# -----------------------------------------------------------------------------

class OBJECT_PT_change_sds_uv_smooth(bpy.types.Panel):
    # The identifier is kept from the former stand-alone panel.
    bl_label = "UV Smooth"
    bl_idname = "OBJECT_PT_change_sds_uv_smooth"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = eterea_ui.SIDEBAR_CATEGORY
    bl_parent_id = SUBDIVISION_PANEL_ID

    def draw(self, context):
        layout = self.layout

        layout.operator(
            "object.set_uv_smooth_boundaries",
            text="Keep Boundaries",
            icon='SHAPEKEY_DATA'
        )

        layout.operator(
            "object.set_uv_smooth_corners",
            text="Keep Corners",
            icon='MESH_GRID'
        )


# -----------------------------------------------------------------------------
# Operators (one per UV Smooth mode, sharing the same logic)
# -----------------------------------------------------------------------------

class _UVSmoothOperatorMixin:
    bl_options = {'REGISTER', 'UNDO'}
    uv_smooth = ''      # value of SubsurfModifier.uv_smooth
    mode_label = ""     # name shown in the report

    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects)

    def execute(self, context):
        count = 0

        for obj in context.selected_objects:
            for mod in obj.modifiers:
                if mod.type == 'SUBSURF':
                    mod.uv_smooth = self.uv_smooth
                    count += 1

        self.report({'INFO'}, f"{count} Subdivision modifiers set to {self.mode_label}")
        return {'FINISHED'}


class OBJECT_OT_set_uv_smooth_boundaries(_UVSmoothOperatorMixin, bpy.types.Operator):
    bl_label = "Set UV Smooth: Keep Boundaries"
    bl_idname = "object.set_uv_smooth_boundaries"
    bl_description = "Set UV Smooth to Keep Boundaries for all selected objects"
    uv_smooth = 'PRESERVE_BOUNDARIES'
    mode_label = "Keep Boundaries"


class OBJECT_OT_set_uv_smooth_corners(_UVSmoothOperatorMixin, bpy.types.Operator):
    bl_label = "Set UV Smooth: Keep Corners"
    bl_idname = "object.set_uv_smooth_corners"
    bl_description = "Set UV Smooth to Keep Corners for all selected objects"
    uv_smooth = 'PRESERVE_CORNERS'
    mode_label = "Keep Corners"


# -----------------------------------------------------------------------------
# Registration
# -----------------------------------------------------------------------------

classes = (
    OBJECT_PT_change_sds_uv_smooth,
    OBJECT_OT_set_uv_smooth_boundaries,
    OBJECT_OT_set_uv_smooth_corners,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
