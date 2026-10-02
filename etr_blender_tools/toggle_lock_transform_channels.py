# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Cristobal Vila (etereaestudios.com)

"""
Toggle Lock Channels for Selected

Eight items (4 Lock + 4 Unlock) added directly to the shared "Eterea Tools"
submenu (see eterea_ui.py), both in the 3D Viewport and in the Outliner. Works on
any object type, because lock_location / lock_rotation / lock_scale belong to
bpy.types.Object itself. Rotation locks include W (lock_rotation_w), used by
Quaternion and Axis Angle rotations.
"""

bl_info = {
    "name": "Toggle Lock Channels for Selected",
    "author": "Idea by Cristobal Vila / Code by Claude.ai",
    "version": (2, 0, 2),
    "blender": (5, 2, 0),
    "location": "3D Viewport (Object Mode) / Outliner > Right-Click > Eterea Tools",
    "description": (
        "Lock or unlock the Transform channels (all, or just Location, Rotation "
        "or Scale) of every selected object."
    ),
    "category": "Object",
}

import bpy

from . import eterea_ui


# -----------------------------------------------------------------------------
# Core operator
# -----------------------------------------------------------------------------

_CHANNEL_LABELS = {
    'ALL': "Transform",
    'LOCATION': "Location",
    'ROTATION': "Rotation",
    'SCALE': "Scale",
}


class OBJECT_OT_set_lock_transform_channels_selected(bpy.types.Operator):
    """Lock or unlock Transform channels for every selected object.
    Works on any object type (Mesh, Empty, Camera, Light, Curve, Armature, etc.)
    because lock_location / lock_rotation / lock_scale exist on bpy.types.Object
    itself, regardless of the object's data type."""

    bl_idname = "object.set_lock_transform_channels_selected"
    bl_label = "Set Lock Transform Channels for Selected"
    bl_options = {'REGISTER', 'UNDO'}

    lock: bpy.props.BoolProperty(
        name="Lock",
        description="True to lock the channels, False to unlock them",
        default=True,
    )
    channel: bpy.props.EnumProperty(
        name="Channel",
        description="Which Transform channel(s) to affect",
        items=(
            ('ALL', "All", "Location, Rotation and Scale"),
            ('LOCATION', "Location", "Location only"),
            ('ROTATION', "Rotation", "Rotation only"),
            ('SCALE', "Scale", "Scale only"),
        ),
        default='ALL',
    )

    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects)

    def execute(self, context):
        state = self.lock
        channel = self.channel
        count = 0
        for obj in context.selected_objects:
            if channel in ('ALL', 'LOCATION'):
                obj.lock_location = (state, state, state)
            if channel in ('ALL', 'ROTATION'):
                obj.lock_rotation = (state, state, state)
                obj.lock_rotation_w = state
            if channel in ('ALL', 'SCALE'):
                obj.lock_scale = (state, state, state)
            count += 1

        action = "Locked" if state else "Unlocked"
        channel_label = _CHANNEL_LABELS[channel]
        noun = "object" if count == 1 else "objects"
        self.report({'INFO'}, f"{action} {channel_label} channels on {count} {noun}")
        return {'FINISHED'}


# -----------------------------------------------------------------------------
# "Eterea Tools" submenu section (see eterea_ui.py)
# -----------------------------------------------------------------------------

def draw_eterea_tools_section(layout, context):
    idname = OBJECT_OT_set_lock_transform_channels_selected.bl_idname

    def add_item(text, icon, lock, channel):
        op = layout.operator(idname, text=text, icon=icon)
        op.lock = lock
        op.channel = channel

    add_item("Lock All Transform Channels for Selected", 'LOCKED', True, 'ALL')
    add_item("Lock Location Channels for Selected", 'LOCKED', True, 'LOCATION')
    add_item("Lock Rotation Channels for Selected", 'LOCKED', True, 'ROTATION')
    add_item("Lock Scale Channels for Selected", 'LOCKED', True, 'SCALE')

    layout.separator()

    add_item("Unlock All Transform Channels for Selected", 'UNLOCKED', False, 'ALL')
    add_item("Unlock Location Channels for Selected", 'UNLOCKED', False, 'LOCATION')
    add_item("Unlock Rotation Channels for Selected", 'UNLOCKED', False, 'ROTATION')
    add_item("Unlock Scale Channels for Selected", 'UNLOCKED', False, 'SCALE')


# Both the 3D Viewport (Object Mode) and the Outliner right-click menus.
_CONTEXTS = (
    eterea_ui.OBJECT_CONTEXT,
    eterea_ui.OUTLINER_CONTEXT,
)


# -----------------------------------------------------------------------------
# Registration
# -----------------------------------------------------------------------------

classes = (
    OBJECT_OT_set_lock_transform_channels_selected,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    for context_id in _CONTEXTS:
        eterea_ui.add_section(context_id, __name__, draw_eterea_tools_section)


def unregister():
    for context_id in _CONTEXTS:
        eterea_ui.remove_section(context_id, __name__)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

