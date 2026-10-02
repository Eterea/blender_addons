# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Cristobal Vila (etereaestudios.com)

"""
Batch Operate Attributes

Two operators, each opening a small dialog, that work on every selected Mesh,
Curves (the new hair / Geometry Nodes curves) and Point Cloud object:
  - Rename Attribute on Selected Objects: renames an attribute (exact name).
    Objects that already have an attribute with the new name are skipped, so
    nothing is ever overwritten.
  - Delete Attribute on Selected Objects: removes an attribute (exact name).

The attribute name field offers a searchable list of the attributes found on
the selected objects (with their domain, type and on how many objects they
exist), but any name can still be typed. Internal attributes (names starting
with ".") are not listed.

Objects that share their data (linked duplicates) are processed and counted
once. Legacy Curve objects (Bezier / NURBS) have no generic attributes, so
they are ignored.

Both items live in the shared "Eterea Tools" submenu (see eterea_ui.py), in the
3D Viewport and Outliner right-click menus, and are only shown in Object Mode
when at least one supported object is selected.
"""

bl_info = {
    "name": "Batch Operate Attributes",
    "author": "Idea by Cristobal Vila / Code by Claude.ai",
    "version": (1, 2, 0),
    "blender": (5, 2, 0),
    "location": "3D Viewport (Object Mode) / Outliner > Right-Click > Eterea Tools",
    "description": (
        "Rename or delete an attribute across all selected Mesh, Curves and "
        "Point Cloud objects."
    ),
    "category": "Object",
}

import bpy

from . import eterea_ui

# Object types whose data has generic attributes.
SUPPORTED_TYPES = {'MESH', 'CURVES', 'POINTCLOUD'}


def selected_data(context):
    """Return the data of the selected supported objects, without repeats.

    Several objects can share their data (linked duplicates); each data-block
    is processed and counted once.
    """
    data_blocks = []
    for obj in context.selected_objects:
        if obj.type in SUPPORTED_TYPES and obj.data not in data_blocks:
            data_blocks.append(obj.data)
    return data_blocks


def _has_supported_selection(context):
    return context.mode == 'OBJECT' and any(
        obj.type in SUPPORTED_TYPES for obj in context.selected_objects
    )


def _plural(count, word):
    return f"{count} {word}{'' if count == 1 else 's'}"


def _search_attribute_names(self, context, edit_text):
    """Suggestions for the attribute name fields: names found on the selection.

    Each suggestion shows the domain and type of the attribute, and on how many
    of the selected objects it exists.
    """
    data_blocks = selected_data(context)
    found = {}  # name -> [domain, data_type, count]
    for data in data_blocks:
        for attr in data.attributes:
            if attr.name.startswith("."):
                continue
            info = found.setdefault(attr.name, [attr.domain, attr.data_type, 0])
            info[2] += 1

    total = len(data_blocks)
    text = edit_text.lower()
    suggestions = []
    for name, (domain, data_type, count) in found.items():
        if text and text not in name.lower():
            continue
        description = f"{domain.title()} · {data_type.title()} · {count} of {total}"
        suggestions.append((name, description))
    return suggestions


class BATCH_OPERATE_ATTRIBUTES_OT_rename_attribute(bpy.types.Operator):
    bl_idname = "batch_operate_attributes.rename_attribute"
    bl_label = "Rename Attribute on Selected Objects"
    bl_description = (
        "Rename an attribute on all selected Mesh, Curves and Point Cloud objects"
    )
    bl_options = {'REGISTER', 'UNDO'}

    search_name: bpy.props.StringProperty(
        name="Search for this Attribute Name",
        description="Exact name of the attribute to rename (pick it from the list or type it)",
        default="",
        search=_search_attribute_names,
        search_options={'SORT', 'SUGGESTION'},
    )

    replace_name: bpy.props.StringProperty(
        name="Replace with this Attribute Name",
        description="New name for the attribute",
        default="",
    )

    @classmethod
    def poll(cls, context):
        return _has_supported_selection(context)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(
            self,
            width=460,
        )

    def draw(self, context):
        layout = self.layout
        layout.label(text="RENAME ATTRIBUTE ON SELECTED", icon='SORTALPHA')
        layout.separator(factor=0.5)

        col = layout.column(align=False)
        col.prop(self, "search_name")
        col.prop(self, "replace_name")

    def execute(self, context):
        search = self.search_name
        replace = self.replace_name

        if not search or not replace:
            self.report({'WARNING'}, "Both attribute names are needed")
            return {'CANCELLED'}
        if search == replace:
            self.report({'WARNING'}, "The new name is the same as the current one")
            return {'CANCELLED'}

        renamed = collisions = rejected = 0

        # Attribute values/data are untouched: only Attribute.name is assigned.
        for data in selected_data(context):
            attr = data.attributes.get(search)

            if attr is None:
                continue

            # Avoid collisions. If the destination already exists on this
            # data-block, do not replace or overwrite it.
            if data.attributes.get(replace) is not None:
                collisions += 1
                continue

            try:
                attr.name = replace
            except (AttributeError, RuntimeError):
                # Keep the operation non-destructive if Blender rejects the
                # requested name for any reason (e.g. a built-in attribute).
                rejected += 1
                continue

            renamed += 1

        if renamed == 0 and collisions == 0 and rejected == 0:
            self.report({'WARNING'}, f'Attribute "{search}" not found on any selected object')
            return {'CANCELLED'}

        message = f'Attribute "{search}" renamed to "{replace}" on {_plural(renamed, "object")}'
        skipped = []
        if collisions:
            skipped.append(f"{collisions} skipped (\"{replace}\" already exists)")
        if rejected:
            skipped.append(f"{rejected} could not be renamed (built-in attribute)")
        if skipped:
            message += "; " + ", ".join(skipped)
        self.report({'WARNING'} if skipped else {'INFO'}, message)
        return {'FINISHED'} if renamed else {'CANCELLED'}


class BATCH_OPERATE_ATTRIBUTES_OT_delete_attribute(bpy.types.Operator):
    bl_idname = "batch_operate_attributes.delete_attribute"
    bl_label = "Delete Attribute on Selected Objects"
    bl_description = (
        "Delete an attribute from all selected Mesh, Curves and Point Cloud objects"
    )
    bl_options = {'REGISTER', 'UNDO'}

    search_name: bpy.props.StringProperty(
        name="Search for this Attribute Name",
        description="Exact name of the attribute to delete (pick it from the list or type it)",
        default="",
        search=_search_attribute_names,
        search_options={'SORT', 'SUGGESTION'},
    )

    @classmethod
    def poll(cls, context):
        return _has_supported_selection(context)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(
            self,
            width=460,
        )

    def draw(self, context):
        layout = self.layout
        layout.label(text="DELETE ATTRIBUTE ON SELECTED", icon='TRASH')
        layout.separator(factor=0.5)

        col = layout.column(align=False)
        col.prop(self, "search_name")

    def execute(self, context):
        search = self.search_name

        if not search:
            self.report({'WARNING'}, "An attribute name is needed")
            return {'CANCELLED'}

        deleted = rejected = 0

        for data in selected_data(context):
            attr = data.attributes.get(search)

            if attr is None:
                continue

            try:
                data.attributes.remove(attr)
            except (AttributeError, RuntimeError):
                # Built-in attributes (e.g. "position") cannot be removed.
                rejected += 1
                continue

            deleted += 1

        if deleted == 0 and rejected == 0:
            self.report({'WARNING'}, f'Attribute "{search}" not found on any selected object')
            return {'CANCELLED'}

        message = f'Attribute "{search}" deleted from {_plural(deleted, "object")}'
        if rejected:
            message += f"; {rejected} could not be deleted (built-in attribute)"
        self.report({'WARNING'} if rejected else {'INFO'}, message)
        return {'FINISHED'} if deleted else {'CANCELLED'}


# -----------------------------------------------------------------------------
# "Eterea Tools" submenu section (see eterea_ui.py)
# -----------------------------------------------------------------------------

def poll_eterea_tools_section(context):
    """Only show the items in Object Mode with a supported object selected."""
    return _has_supported_selection(context)


def draw_eterea_tools_section(layout, context):
    layout.operator(
        BATCH_OPERATE_ATTRIBUTES_OT_rename_attribute.bl_idname,
        text="Rename Attribute on Selected Objects",
        icon='SORTALPHA',
    )
    layout.operator(
        BATCH_OPERATE_ATTRIBUTES_OT_delete_attribute.bl_idname,
        text="Delete Attribute on Selected Objects",
        icon='TRASH',
    )


classes = (
    BATCH_OPERATE_ATTRIBUTES_OT_rename_attribute,
    BATCH_OPERATE_ATTRIBUTES_OT_delete_attribute,
)

# Both the 3D Viewport (Object Mode) and the Outliner right-click menus.
_CONTEXTS = (
    eterea_ui.OBJECT_CONTEXT,
    eterea_ui.OUTLINER_CONTEXT,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    for context_id in _CONTEXTS:
        eterea_ui.add_section(
            context_id,
            __name__,
            draw_eterea_tools_section,
            poll_eterea_tools_section,
        )


def unregister():
    for context_id in _CONTEXTS:
        eterea_ui.remove_section(context_id, __name__)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
