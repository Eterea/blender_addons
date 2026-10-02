# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Cristobal Vila (etereaestudios.com)

"""
Copy Viewport Color

Adds "Copy Viewport Color" to the Link/Transfer Data menu (Ctrl+L / Cmd+L).
It copies Object Properties > Viewport Display > Color from the active object
to every other selected object, whatever their type. If that menu ever
disappears in a future Blender version, the item falls back to the 3D Viewport
right-click menu automatically.
"""

bl_info = {
    "name": "Copy Viewport Color",
    "author": "Idea by Cristobal Vila / Code by Claude.ai",
    "version": (1, 0, 2),
    "blender": (5, 2, 0),
    "location": "3D Viewport > Object > Link/Transfer Data (Ctrl+L)",
    "description": (
        "Copy the Viewport Display Color of the active object to all the other "
        "selected objects."
    ),
    "category": "Object",
}

import bpy


class OBJECT_OT_copy_viewport_color(bpy.types.Operator):
    """Copy the Viewport Display Color of the active object to the other selected objects"""
    bl_idname = "object.copy_viewport_color"
    bl_label = "Copy Viewport Color"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # An active object and at least one other selected object are required
        return (
            context.active_object is not None
            and len(context.selected_objects) > 1
        )

    def execute(self, context):
        active_obj = context.active_object
        color = tuple(active_obj.color)  # RGBA

        targets = [obj for obj in context.selected_objects if obj != active_obj]

        # obj.color (Viewport Display > Color) exists on every object type
        # (Mesh, Curve, Surface, Metaball, Font, etc.), so there is no need to
        # filter by type. The poll guarantees at least one target.
        for obj in targets:
            obj.color = color
        count = len(targets)

        self.report(
            {'INFO'},
            f"Viewport Color copied from '{active_obj.name}' to {count} object(s)"
        )
        return {'FINISHED'}


def menu_func(self, context):
    """Menu entry, used in whichever menu the item is added to."""
    layout = self.layout
    layout.separator()
    layout.operator(
        OBJECT_OT_copy_viewport_color.bl_idname,
        text="Copy Viewport Color",
    )


classes = (OBJECT_OT_copy_viewport_color,)

# Class name of the "Link/Transfer Data" menu (Ctrl+L / Cmd+L).
# It has been stable for many Blender versions, but in case it is renamed or
# removed in the future, registration is done safely: if it does not exist,
# the item automatically falls back to the 3D Viewport right-click menu
# (plan B).
_LINK_MENU_ID = "VIEW3D_MT_make_links"
_CONTEXT_MENU_ID = "VIEW3D_MT_object_context_menu"

_registered_in_link_menu = False
_registered_in_context_menu = False


def register():
    global _registered_in_link_menu, _registered_in_context_menu

    for cls in classes:
        bpy.utils.register_class(cls)

    link_menu = getattr(bpy.types, _LINK_MENU_ID, None)
    if link_menu is not None:
        link_menu.append(menu_func)
        _registered_in_link_menu = True
    else:
        # Plan B: if the Ctrl+L menu does not exist with that identifier,
        # add the item to the 3D Viewport right-click context menu instead.
        context_menu = getattr(bpy.types, _CONTEXT_MENU_ID, None)
        if context_menu is not None:
            context_menu.append(menu_func)
            _registered_in_context_menu = True


def unregister():
    global _registered_in_link_menu, _registered_in_context_menu

    if _registered_in_link_menu:
        link_menu = getattr(bpy.types, _LINK_MENU_ID, None)
        if link_menu is not None:
            link_menu.remove(menu_func)
        _registered_in_link_menu = False

    if _registered_in_context_menu:
        context_menu = getattr(bpy.types, _CONTEXT_MENU_ID, None)
        if context_menu is not None:
            context_menu.remove(menu_func)
        _registered_in_context_menu = False

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
