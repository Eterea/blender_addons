# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Cristobal Vila (etereaestudios.com)

"""
Weight Ramp by Order

Panel "Weight Ramp by Order" with a single button. In Edit Mode, click the
vertices one by one (first click, then Shift+click the rest, in order) and
press the button: a new Vertex Group ("ETR VertSelOrder 000", 001, ...) is
created with weights ramping linearly from 0 (first vertex) to 1 (last
vertex), and the object is switched to Weight Paint Mode to preview the
result.

The selection order is read from Blender's own selection history
(BMesh.select_history), which records every vertex picked with a click. So no
modal capture, timer or Esc key is needed. Vertices selected in other ways
(Box Select, Select All, Select Linked...) are not in the history: they are
ignored and reported.
"""

bl_info = {
    "name": "Weight Ramp by Order",
    "author": "Idea by Cristobal Vila / Code by Claude.ai",
    "version": (2, 0, 2),
    "blender": (5, 2, 0),
    "location": "3D Viewport > Sidebar (N) > Eterea Tools",
    "description": (
        "Create a Vertex Group with a linear weight ramp (0 to 1) following the "
        "order in which the vertices are selected."
    ),
    "category": "Object",
}

import bpy
import bmesh

from . import eterea_ui

# Base name of the created Vertex Groups ("ETR VertSelOrder 000", 001, ...).
GROUP_BASE_NAME = "ETR VertSelOrder"


def _unique_group_name(obj):
    """Return the first free "ETR VertSelOrder NNN" name on `obj`."""
    suffix = 0
    while obj.vertex_groups.get(f"{GROUP_BASE_NAME} {suffix:03}"):
        suffix += 1
    return f"{GROUP_BASE_NAME} {suffix:03}"


def _ramp_weights(count):
    """Return `count` weights ramping linearly from 0 (first) to 1 (last)."""
    if count == 1:
        return [1.0]
    return [i / (count - 1) for i in range(count)]


class OBJECT_OT_capture_selection_order(bpy.types.Operator):
    """Create a Vertex Group whose weights follow the order in which the vertices were clicked"""
    # The identifier is kept from the earlier modal version, so shortcuts and
    # Quick Favorites keep working.
    bl_idname = "object.capture_selection_order"
    bl_label = "Create Weight Ramp from Selection Order"
    # 'UNDO' only (no 'REGISTER'): the operator has no options, so there is
    # no "Adjust Last Operation" (F9) panel.
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (
            context.mode == 'EDIT_MESH'
            and obj is not None
            and obj.type == 'MESH'
        )

    def execute(self, context):
        obj = context.active_object
        bm = bmesh.from_edit_mesh(obj.data)
        bm.verts.index_update()  # make sure v.index matches the mesh order

        # Vertices in click order, without repetitions.
        order = []
        seen = set()
        for elem in bm.select_history:
            if isinstance(elem, bmesh.types.BMVert) and elem.index not in seen:
                seen.add(elem.index)
                order.append(elem)

        if not order:
            self.report(
                {'WARNING'},
                "No click order found: in Vertex Select mode, click the first "
                "vertex and Shift+click the rest, in order",
            )
            return {'CANCELLED'}

        selected_count = sum(1 for v in bm.verts if v.select)
        ignored = selected_count - len(order)
        indices = [v.index for v in order]
        weights = _ramp_weights(len(indices))

        # Vertex weights are assigned in Object Mode.
        bpy.ops.object.mode_set(mode='OBJECT')

        group_name = _unique_group_name(obj)
        vgroup = obj.vertex_groups.new(name=group_name)
        for index, weight in zip(indices, weights):
            vgroup.add([index], weight, 'REPLACE')

        # Switch to Weight Paint Mode for visualization.
        bpy.ops.object.mode_set(mode='WEIGHT_PAINT')

        message = f"Vertex Group '{group_name}' created from {len(indices)} vertices"
        if ignored > 0:
            message += f" ({ignored} selected vertices had no click order and were ignored)"
            self.report({'WARNING'}, message)
        else:
            self.report({'INFO'}, message)
        return {'FINISHED'}


class OBJECT_PT_weight_ramp(bpy.types.Panel):
    """Panel in the Eterea Tools tab of the 3D Viewport Sidebar (N)"""
    bl_label = "Weight Ramp by Order"
    bl_idname = "OBJECT_PT_weight_ramp"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = eterea_ui.SIDEBAR_CATEGORY

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.label(text="In Edit Mode, click the vertices")
        col.label(text="in order (Shift+click), then:")
        layout.operator(
            OBJECT_OT_capture_selection_order.bl_idname,
            text="Create Weight Ramp",
            icon='IPO_LINEAR',
        )


classes = (
    OBJECT_OT_capture_selection_order,
    OBJECT_PT_weight_ramp,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
