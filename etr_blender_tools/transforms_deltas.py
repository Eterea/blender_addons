# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Cristobal Vila (etereaestudios.com)

"""
Transform and Deltas

Sub-panel "Manage Deltas" inside the Object Properties Transform panel, laid
out in two compact columns:
  - Left column (down triangle): "All Transforms to Deltas" on top, and below
    it Loc / Rot / Scale buttons that move each transform into its delta.
  - Right column (up triangle): "Reset All Deltas" on top, and below it
    Loc / Rot / Scale buttons that merge each delta back into the regular
    transform (the object does not move).

Rotation works with Euler and Quaternion rotation modes, in both directions.
Axis Angle has no delta rotation in Blender, so it is left untouched and
reported.
"""

bl_info = {
    "name": "Transform and Deltas",
    "author": "Idea by Cristobal Vila / Code by Claude.ai",
    "version": (1, 5, 0),
    "blender": (5, 2, 0),
    "location": "Properties > Object > Transform > Manage Deltas",
    "description": (
        "Move transforms to deltas, or merge deltas back into transforms, for "
        "the selected objects."
    ),
    "category": "Object",
}

import bpy
from mathutils import Quaternion

# Rotation modes handled by the rotation buttons: the six Euler orders and
# Quaternion. Axis Angle has no delta rotation in Blender, so it is left
# untouched and reported.
EULER_MODES = {'XYZ', 'XZY', 'YXZ', 'YZX', 'ZXY', 'ZYX'}
SUPPORTED_ROTATION_MODES = EULER_MODES | {'QUATERNION'}


# ---------------------------------------------------------------------------
# Core logic
#
# Blender composes the final transform as:
#   location = location + delta_location
#   rotation = delta_rotation @ rotation   (as matrices, or as normalized
#                                           quaternions in Quaternion mode)
#   scale    = scale * delta_scale
# so moving values between the two never moves the object.
# ---------------------------------------------------------------------------

def _combined_euler(obj, compatible):
    """Return delta rotation @ rotation as an Euler in the object's order.

    `compatible` is the Euler the result should stay close to, so that full
    turns (e.g. 370 degrees) are not folded back to 10 degrees.
    """
    matrix = obj.delta_rotation_euler.to_matrix() @ obj.rotation_euler.to_matrix()
    return matrix.to_euler(obj.rotation_euler.order, compatible)


def _combined_quaternion(obj):
    """Return delta rotation @ rotation, both normalized, as Blender does."""
    delta = Quaternion(obj.delta_rotation_quaternion).normalized()
    rotation = Quaternion(obj.rotation_quaternion).normalized()
    return delta @ rotation


def location_to_deltas(obj):
    obj.delta_location += obj.location
    obj.location = (0.0, 0.0, 0.0)


def rotation_to_deltas(obj):
    if obj.rotation_mode == 'QUATERNION':
        obj.delta_rotation_quaternion = _combined_quaternion(obj)
        obj.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
    else:
        obj.delta_rotation_euler = _combined_euler(obj, obj.delta_rotation_euler)
        obj.rotation_euler = (0.0, 0.0, 0.0)


def scale_to_deltas(obj):
    obj.delta_scale = [d * s for d, s in zip(obj.delta_scale, obj.scale)]
    obj.scale = (1.0, 1.0, 1.0)


def reset_location_deltas(obj):
    obj.location += obj.delta_location
    obj.delta_location = (0.0, 0.0, 0.0)


def reset_rotation_deltas(obj):
    if obj.rotation_mode == 'QUATERNION':
        obj.rotation_quaternion = _combined_quaternion(obj)
        obj.delta_rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
    else:
        obj.rotation_euler = _combined_euler(obj, obj.rotation_euler)
        obj.delta_rotation_euler = (0.0, 0.0, 0.0)


def reset_scale_deltas(obj):
    obj.scale = [s * d for s, d in zip(obj.scale, obj.delta_scale)]
    obj.delta_scale = (1.0, 1.0, 1.0)


_TO_DELTAS = {
    'LOCATION': location_to_deltas,
    'ROTATION': rotation_to_deltas,
    'SCALE': scale_to_deltas,
}
_RESET_DELTAS = {
    'LOCATION': reset_location_deltas,
    'ROTATION': reset_rotation_deltas,
    'SCALE': reset_scale_deltas,
}


class _DeltasOperatorMixin:
    """Shared poll / execute of the 8 operators.

    Each operator only sets `channels` (which transforms it affects) and
    `to_deltas` (True: transform -> delta, False: delta -> transform).
    """
    bl_options = {'REGISTER', 'UNDO'}
    channels = ()
    to_deltas = True

    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects)

    def execute(self, context):
        functions = _TO_DELTAS if self.to_deltas else _RESET_DELTAS
        objects = list(context.selected_objects)
        skipped = 0
        for obj in objects:
            for channel in self.channels:
                if channel == 'ROTATION' and obj.rotation_mode not in SUPPORTED_ROTATION_MODES:
                    skipped += 1
                    continue
                functions[channel](obj)

        if skipped:
            noun = "object" if skipped == 1 else "objects"
            self.report(
                {'WARNING'},
                f"Rotation left unchanged on {skipped} {noun} using Axis Angle "
                "rotation (Blender has no delta rotation for Axis Angle)",
            )
        return {'FINISHED'}


# Operators: transform -> deltas
class OBJECT_OT_location_to_deltas(_DeltasOperatorMixin, bpy.types.Operator):
    bl_idname = "object.location_to_deltas"
    bl_label = "Location to Deltas"
    bl_description = "Move location to delta and reset location"
    channels = ('LOCATION',)


class OBJECT_OT_rotation_to_deltas(_DeltasOperatorMixin, bpy.types.Operator):
    bl_idname = "object.rotation_to_deltas"
    bl_label = "Rotation to Deltas"
    bl_description = "Move rotation to delta and reset rotation"
    channels = ('ROTATION',)


class OBJECT_OT_scale_to_deltas(_DeltasOperatorMixin, bpy.types.Operator):
    bl_idname = "object.scale_to_deltas"
    bl_label = "Scale to Deltas"
    bl_description = "Move scale to delta and reset scale"
    channels = ('SCALE',)


class OBJECT_OT_all_transforms_to_deltas(_DeltasOperatorMixin, bpy.types.Operator):
    bl_idname = "object.all_transforms_to_deltas"
    bl_label = "All Transforms to Deltas"
    bl_description = "Move all transforms to deltas and reset transforms"
    channels = ('LOCATION', 'ROTATION', 'SCALE')


# Operators: deltas -> transform
class OBJECT_OT_reset_location_deltas(_DeltasOperatorMixin, bpy.types.Operator):
    bl_idname = "object.reset_location_deltas"
    bl_label = "Reset Location Deltas"
    bl_description = "Combine and reset location deltas"
    channels = ('LOCATION',)
    to_deltas = False


class OBJECT_OT_reset_rotation_deltas(_DeltasOperatorMixin, bpy.types.Operator):
    bl_idname = "object.reset_rotation_deltas"
    bl_label = "Reset Rotation Deltas"
    bl_description = "Combine and reset rotation deltas"
    channels = ('ROTATION',)
    to_deltas = False


class OBJECT_OT_reset_scale_deltas(_DeltasOperatorMixin, bpy.types.Operator):
    bl_idname = "object.reset_scale_deltas"
    bl_label = "Reset Scale Deltas"
    bl_description = "Combine and reset scale deltas"
    channels = ('SCALE',)
    to_deltas = False


class OBJECT_OT_reset_all_deltas(_DeltasOperatorMixin, bpy.types.Operator):
    bl_idname = "object.reset_all_deltas"
    bl_label = "Reset All Deltas"
    bl_description = "Combine and reset all deltas"
    channels = ('LOCATION', 'ROTATION', 'SCALE')
    to_deltas = False


# Panel in Object Properties > Transform section
class OBJECT_PT_manage_deltas(bpy.types.Panel):
    bl_idname = "OBJECT_PT_manage_deltas"
    bl_label = "Manage Deltas"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    bl_parent_id = "OBJECT_PT_transform"

    def draw(self, context):
        layout = self.layout
        split = layout.split(factor=0.5)

        # Left column: transforms -> deltas (down triangle)
        col_left = split.column()
        col_left.operator("object.all_transforms_to_deltas", text="\u25BD All Transforms to Deltas")
        row_left = col_left.row(align=True)
        row_left.operator("object.location_to_deltas", text="\u25BD Loc")
        row_left.operator("object.rotation_to_deltas", text="\u25BD Rot")
        row_left.operator("object.scale_to_deltas", text="\u25BD Scale")

        # Right column: deltas -> transforms (up triangle)
        col_right = split.column()
        col_right.operator("object.reset_all_deltas", text="\u25B3 Reset All Deltas")
        row_right = col_right.row(align=True)
        row_right.operator("object.reset_location_deltas", text="\u25B3 Loc")
        row_right.operator("object.reset_rotation_deltas", text="\u25B3 Rot")
        row_right.operator("object.reset_scale_deltas", text="\u25B3 Scale")


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

classes = (
    OBJECT_OT_location_to_deltas,
    OBJECT_OT_rotation_to_deltas,
    OBJECT_OT_scale_to_deltas,
    OBJECT_OT_all_transforms_to_deltas,
    OBJECT_OT_reset_location_deltas,
    OBJECT_OT_reset_rotation_deltas,
    OBJECT_OT_reset_scale_deltas,
    OBJECT_OT_reset_all_deltas,
    OBJECT_PT_manage_deltas,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
