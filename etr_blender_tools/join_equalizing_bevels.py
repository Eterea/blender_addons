# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Cristobal Vila (etereaestudios.com)

"""
Join Equalizing Bevels

Before joining, the highest Bevel modifier Amount (H) among the selected objects
is found. Each object's edge bevel weights are multiplied by its own Amount / H,
so after the join (where only one Bevel modifier remains, set to H) every part
keeps its original bevel size.

Requirements and limits (checked before anything is changed):
  - Object Mode, an active mesh object and at least one other selected mesh.
  - The active object must have a Bevel modifier (it is the one that remains).
  - The highest Amount must be greater than 0.
  - A mesh whose weights have to be rescaled must not be shared with other
    objects (linked duplicates), or the change would also affect them.
Only the first Bevel modifier of each object is used, and the method assumes
Bevel modifiers limited by Weight and applied to Edges, on objects with the
same scale.
"""

bl_info = {
    "name": "Join Equalizing Bevels",
    "author": "Idea by Cristobal Vila / Code by Claude.ai",
    "version": (1, 2, 1),
    "blender": (5, 2, 0),
    "location": "3D Viewport > Sidebar (N) > Eterea Tools",
    "description": (
        "Join the selected objects, rescaling their edge Bevel Weights so the "
        "result matches the highest Bevel modifier amount."
    ),
    "category": "Object",
}

import bpy

from . import eterea_ui

# Name of the edge bevel weight attribute.
BEVEL_WEIGHT_ATTR = "bevel_weight_edge"


def _first_bevel(obj):
    """Return the first Bevel modifier of `obj`, or None."""
    return next((mod for mod in obj.modifiers if mod.type == 'BEVEL'), None)


def _read_weights(mesh):
    """Return the edge bevel weights of `mesh` as a list, or None."""
    attr = mesh.attributes.get(BEVEL_WEIGHT_ATTR)
    if attr is None or attr.domain != 'EDGE' or attr.data_type != 'FLOAT':
        return None
    values = [0.0] * len(attr.data)
    attr.data.foreach_get("value", values)
    return values


def _write_weights(mesh, values):
    mesh.attributes[BEVEL_WEIGHT_ATTR].data.foreach_set("value", values)


class OBJECT_OT_join_equalizing_bevels(bpy.types.Operator):
    bl_idname = "object.join_equalizing_bevels"
    bl_label = "Join Equalizing Bevels"
    bl_description = "Join selected objects, adjusting bevel weights proportionally to the highest Bevel Modifier amount"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        active = context.active_object
        return (
            context.mode == 'OBJECT'
            and active is not None
            and active.type == 'MESH'
            and active in context.selected_objects
            and sum(1 for obj in context.selected_objects if obj.type == 'MESH') > 1
        )

    def execute(self, context):
        active = context.active_object
        # Only meshes are joined into a mesh, so only meshes are processed.
        objects = [active] + [
            obj for obj in context.selected_objects
            if obj.type == 'MESH' and obj != active
        ]

        active_bevel = _first_bevel(active)
        if active_bevel is None:
            self.report(
                {'WARNING'},
                f"The active object '{active.name}' needs a Bevel modifier "
                "(it is the one kept after the join)",
            )
            return {'CANCELLED'}

        bevels = {obj: _first_bevel(obj) for obj in objects}
        highest = max(mod.width for mod in bevels.values() if mod is not None)
        if highest <= 0.0:
            self.report({'WARNING'}, "The highest Bevel Amount is 0: nothing to equalize")
            return {'CANCELLED'}

        # Work out every change first, so nothing is modified if the
        # operation has to be cancelled.
        to_rescale = []  # (mesh, original weights, factor)
        for obj, mod in bevels.items():
            if mod is None:
                continue
            factor = mod.width / highest
            if factor == 1.0:
                continue
            weights = _read_weights(obj.data)
            if weights is None:
                continue
            if obj.data.users > 1:
                self.report(
                    {'WARNING'},
                    f"'{obj.name}' shares its mesh with other objects. Make it "
                    "single-user first (Object > Relations > Make Single User)",
                )
                return {'CANCELLED'}
            to_rescale.append((obj.data, weights, factor))

        # Bevel modifiers this method does not really apply to (checked now:
        # the joined objects no longer exist after the join).
        not_by_weight = sum(
            1 for mod in bevels.values()
            if mod is not None and (mod.limit_method != 'WEIGHT' or mod.affect != 'EDGES')
        )
        joined_count = len(objects)

        for mesh, weights, factor in to_rescale:
            _write_weights(mesh, [w * factor for w in weights])

        try:
            bpy.ops.object.join()
        except RuntimeError as exc:
            # Put the original weights back before giving up.
            for mesh, weights, _factor in to_rescale:
                if mesh.users:
                    _write_weights(mesh, weights)
            self.report({'ERROR'}, f"Join failed: {exc}")
            return {'CANCELLED'}

        # The active object keeps its own (first) Bevel modifier.
        active_bevel.width = highest

        message = f"Joined {joined_count} objects, Bevel Amount set to {highest:g}"
        if not_by_weight:
            message += (
                f". Note: {not_by_weight} Bevel modifier(s) did not use "
                "Edge Weights, so their size may differ"
            )
            self.report({'WARNING'}, message)
        else:
            self.report({'INFO'}, message)
        return {'FINISHED'}


class OBJECT_PT_join_equalizing_bevels(bpy.types.Panel):
    bl_label = "Join Equalizing Bevels"
    bl_idname = "OBJECT_PT_join_equalizing_bevels"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = eterea_ui.SIDEBAR_CATEGORY

    def draw(self, context):
        layout = self.layout
        layout.operator("object.join_equalizing_bevels")


classes = (
    OBJECT_OT_join_equalizing_bevels,
    OBJECT_PT_join_equalizing_bevels,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
