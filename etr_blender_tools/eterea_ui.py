# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Cristobal Vila (etereaestudios.com)

"""
Eterea UI (shared infrastructure, not a tool by itself)

Common user-interface hooks shared by several tools of the kit:

  - SIDEBAR_CATEGORY: name of the kit's own tab in the 3D Viewport Sidebar (N).
    Blender shows it as "ET" when the Sidebar tabs are collapsed.

  - "Eterea Tools" submenus, appended at the end of some right-click context
    menus (3D Viewport in Object Mode, Outliner, 3D Viewport in Curve Edit Mode,
    and every Node Editor: Shader, Geometry Nodes, Compositor, Texture).
    Each tool registers its own "section" with add_section() and removes it with
    remove_section(). Inside the submenu:
      * all items are listed directly (no nested sub-submenus),
      * sections are drawn in alphabetical order of their owner (module name),
      * consecutive sections are separated by a horizontal line.
    The "Eterea Tools" entry is only shown when at least one section is
    available for the current context, so it never appears empty.

This module must be registered before any tool that uses it and unregistered
after them (see MODULES in __init__.py).
"""

import bpy


# -----------------------------------------------------------------------------
# Public constants
# -----------------------------------------------------------------------------

# Tab name in the 3D Viewport Sidebar (N) for the kit's panels.
SIDEBAR_CATEGORY = "Eterea Tools"

# Label of the right-click submenus.
MENU_LABEL = "Eterea Tools"

# Context identifiers accepted by add_section() / remove_section().
OBJECT_CONTEXT = 'OBJECT_CONTEXT'          # 3D Viewport > Object Mode > Right-Click
OUTLINER_CONTEXT = 'OUTLINER_CONTEXT'      # Outliner > Right-Click
EDIT_CURVE_CONTEXT = 'EDIT_CURVE_CONTEXT'  # 3D Viewport > Curve Edit Mode > Right-Click
NODE_CONTEXT = 'NODE_CONTEXT'              # Any Node Editor > Right-Click


# -----------------------------------------------------------------------------
# Section registry
# -----------------------------------------------------------------------------

# {context_id: {owner: (draw_fn, poll_fn)}}
_sections = {
    OBJECT_CONTEXT: {},
    OUTLINER_CONTEXT: {},
    EDIT_CURVE_CONTEXT: {},
    NODE_CONTEXT: {},
}


def add_section(context_id, owner, draw_fn, poll_fn=None):
    """Add a section of items to one of the "Eterea Tools" submenus.

    context_id: one of OBJECT_CONTEXT, OUTLINER_CONTEXT, EDIT_CURVE_CONTEXT,
                NODE_CONTEXT.
    owner:      unique key for the section (use the tool's __name__). Sections
                are sorted alphabetically by this key.
    draw_fn:    function(layout, context) that draws the section's items.
    poll_fn:    optional function(context) -> bool. When it returns False the
                section is hidden for that context.
    """
    _sections[context_id][owner] = (draw_fn, poll_fn)


def remove_section(context_id, owner):
    """Remove a section previously added with add_section()."""
    _sections[context_id].pop(owner, None)


def _visible_sections(context_id, context):
    """Return the draw functions of the sections available in this context."""
    visible = []
    for owner in sorted(_sections[context_id]):
        draw_fn, poll_fn = _sections[context_id][owner]
        try:
            available = poll_fn is None or poll_fn(context)
        except Exception:
            available = False
        if available:
            visible.append(draw_fn)
    return visible


# -----------------------------------------------------------------------------
# "Eterea Tools" submenus (one per host context)
# -----------------------------------------------------------------------------

# Owners whose section already failed to draw, so each error is printed to the
# console once instead of on every redraw.
_reported_errors = set()


class _EtereaToolsMenuMixin:
    bl_label = MENU_LABEL
    context_id = None

    def draw(self, context):
        layout = self.layout
        for index, draw_fn in enumerate(_visible_sections(self.context_id, context)):
            if index:
                layout.separator()
            try:
                draw_fn(layout, context)
            except Exception as exc:
                # A faulty section must never break the whole menu.
                key = (self.context_id, getattr(draw_fn, "__module__", repr(draw_fn)))
                if key not in _reported_errors:
                    _reported_errors.add(key)
                    print(f"[etr_blender_tools] Eterea Tools menu draw error in {key[1]}: {exc}")


class ETR_MT_eterea_tools_object(_EtereaToolsMenuMixin, bpy.types.Menu):
    bl_idname = "ETR_MT_eterea_tools_object"
    context_id = OBJECT_CONTEXT


class ETR_MT_eterea_tools_outliner(_EtereaToolsMenuMixin, bpy.types.Menu):
    bl_idname = "ETR_MT_eterea_tools_outliner"
    context_id = OUTLINER_CONTEXT


class ETR_MT_eterea_tools_edit_curve(_EtereaToolsMenuMixin, bpy.types.Menu):
    bl_idname = "ETR_MT_eterea_tools_edit_curve"
    context_id = EDIT_CURVE_CONTEXT


class ETR_MT_eterea_tools_node(_EtereaToolsMenuMixin, bpy.types.Menu):
    bl_idname = "ETR_MT_eterea_tools_node"
    context_id = NODE_CONTEXT


# -----------------------------------------------------------------------------
# Hooks into Blender's native right-click menus
# -----------------------------------------------------------------------------

# (native menu name, Eterea Tools submenu class). Menu names can vary slightly
# between Blender versions, so missing ones are silently skipped.
_HOSTS = (
    ("VIEW3D_MT_object_context_menu", ETR_MT_eterea_tools_object),        # 3D Viewport, Object Mode
    ("OUTLINER_MT_object", ETR_MT_eterea_tools_outliner),                 # Outliner, on object(s)
    ("OUTLINER_MT_context_menu", ETR_MT_eterea_tools_outliner),           # Outliner, generic (fallback)
    ("VIEW3D_MT_edit_curve_context_menu", ETR_MT_eterea_tools_edit_curve),  # 3D Viewport, Curve Edit Mode
    ("NODE_MT_context_menu", ETR_MT_eterea_tools_node),                   # Node Editors (Shader, Geometry, Compositor, Texture)
)

# [(native menu class, draw function appended to it)]
_hooked = []


def _make_host_draw(menu_cls):
    """Build the draw function that adds the "Eterea Tools" entry to a native menu."""
    def draw_host_entry(self, context):
        if not _visible_sections(menu_cls.context_id, context):
            return
        layout = self.layout
        layout.separator()
        layout.menu(menu_cls.bl_idname)
    return draw_host_entry


def _hook_menus():
    for menu_name, menu_cls in _HOSTS:
        host_cls = getattr(bpy.types, menu_name, None)
        if host_cls is None:
            continue
        draw_fn = _make_host_draw(menu_cls)
        host_cls.append(draw_fn)
        _hooked.append((host_cls, draw_fn))


def _unhook_menus():
    for host_cls, draw_fn in _hooked:
        try:
            host_cls.remove(draw_fn)
        except (ValueError, RuntimeError):
            pass
    _hooked.clear()


# -----------------------------------------------------------------------------
# Registration
# -----------------------------------------------------------------------------

classes = (
    ETR_MT_eterea_tools_object,
    ETR_MT_eterea_tools_outliner,
    ETR_MT_eterea_tools_edit_curve,
    ETR_MT_eterea_tools_node,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    _hook_menus()


def unregister():
    _unhook_menus()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    for sections in _sections.values():
        sections.clear()
    _reported_errors.clear()
