# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Cristobal Vila (etereaestudios.com)

"""
Set Curve Radius to 1.0

Works on Bezier, Poly and NURBS splines, and on every curve object in multi-object
Edit Mode. The item lives in the shared "Eterea Tools" submenu (see eterea_ui.py).

The menu item always sets 1.0; any other value can then be set in the Adjust
Last Operation panel (F9).
"""

bl_info = {
    "name": "Set Curve Radius to 1.0",
    "author": "Idea by Cristobal Vila / Code by Claude.ai",
    "version": (1, 1, 0),
    "blender": (5, 2, 0),
    "location": "3D Viewport > Curve Edit Mode > Right-Click > Eterea Tools",
    "description": (
        "Set the radius of all selected points to 1.0 (or any value, from the "
        "F9 panel), in every curve object currently in Edit Mode."
    ),
    "category": "Curve",
}

import bpy

from . import eterea_ui


def _selected_points(spline):
    """Yield the selected control points of a Bezier, Poly or NURBS spline."""
    if spline.type == 'BEZIER':
        for point in spline.bezier_points:
            if point.select_control_point:
                yield point
    elif spline.type in {'POLY', 'NURBS'}:
        for point in spline.points:
            if point.select:
                yield point


def set_curve_radius(context, radius_value=1.0):
    """Set the radius of the selected points of every curve in Edit Mode.

    Return the number of points changed.
    """
    count = 0
    for obj in context.objects_in_mode:
        if obj.type != 'CURVE':
            continue
        for spline in obj.data.splines:
            for point in _selected_points(spline):
                point.radius = radius_value
                count += 1
    return count


class CURVE_OT_apply_uniform_radius(bpy.types.Operator):
    """Set the radius of all selected curve points to the same value"""
    bl_idname = "curve.apply_uniform_radius"
    bl_label = "Set Curve Radius"
    bl_options = {'REGISTER', 'UNDO'}

    radius: bpy.props.FloatProperty(
        name="Radius",
        description="Radius given to every selected point",
        default=1.0,
        min=0.0,
        soft_max=10.0,
        step=10,
        precision=3,
    )

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_CURVE'

    def execute(self, context):
        count = set_curve_radius(context, self.radius)
        if count == 0:
            self.report({'WARNING'}, "No curve points selected")
            return {'CANCELLED'}
        noun = "point" if count == 1 else "points"
        self.report({'INFO'}, f"Radius set to {self.radius:g} on {count} {noun}")
        return {'FINISHED'}


# -----------------------------------------------------------------------------
# "Eterea Tools" submenu section (see eterea_ui.py)
# -----------------------------------------------------------------------------

def poll_eterea_tools_section(context):
    return context.object is not None and context.object.type == 'CURVE'


def draw_eterea_tools_section(layout, context):
    # The menu item always starts from 1.0, whatever was used last time.
    op = layout.operator(CURVE_OT_apply_uniform_radius.bl_idname, text="Set Curve Radius to 1.0")
    op.radius = 1.0


def register():
    bpy.utils.register_class(CURVE_OT_apply_uniform_radius)
    eterea_ui.add_section(
        eterea_ui.EDIT_CURVE_CONTEXT,
        __name__,
        draw_eterea_tools_section,
        poll_eterea_tools_section,
    )


def unregister():
    eterea_ui.remove_section(eterea_ui.EDIT_CURVE_CONTEXT, __name__)
    bpy.utils.unregister_class(CURVE_OT_apply_uniform_radius)
