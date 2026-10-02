# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Cristobal Vila (etereaestudios.com)

"""
Eterea Preferences

Shared infrastructure: the single AddonPreferences class of the whole kit
(Blender allows only one per add-on / extension), plus a small registry so
each tool can contribute its own collapsible section to it.

Preferences > Add-ons > Eterea Blender Tools shows one collapsible section per
registered tool ("Custom Color Nodes", ...). Every section is independent and
starts closed, so the full list of sections is always visible at a glance.

How a tool adds its own preferences:
  1. Define a bpy.types.PropertyGroup with the tool's settings, in the tool's
     own module.
  2. Register that group here: add it to TOOL_SETTINGS and add one
     PointerProperty line to EtereaPreferences.
  3. In the tool's register(), call
        preferences.add_section("tool_module", "Section Title", draw_fn)
     and in its unregister(), call
        preferences.remove_section("tool_module")
     where draw_fn(layout, context) draws the section body.

This module is registered right after eterea_ui and before the tools, so the
property groups always exist before any tool needs them.
"""

import bpy
from bpy.props import PointerProperty

from .custom_color_nodes import CustomColorNodesSettings
from .round_values import RoundValuesSettings

# Add-on / extension identifier used to look the preferences up. For an
# Extension this is "bl_ext.<repository>.<extension id>"; for a legacy
# add-on it is the folder name. In both cases it is the package name.
ADDON_ID = __package__

# Property groups registered by this module (before EtereaPreferences).
TOOL_SETTINGS = (
    CustomColorNodesSettings,
    RoundValuesSettings,
)

# owner -> (title, draw function). Filled by the tools in their register().
_sections = {}


def add_section(owner, title, draw_fn):
    """Register (or replace) the preferences section of a tool."""
    _sections[owner] = (title, draw_fn)


def remove_section(owner):
    """Remove the preferences section of a tool, if present."""
    _sections.pop(owner, None)


def get_preferences(context=None):
    """Return the EtereaPreferences instance, or None if it is not available."""
    context = context or bpy.context
    addon = context.preferences.addons.get(ADDON_ID)
    return addon.preferences if addon is not None else None


class EtereaPreferences(bpy.types.AddonPreferences):
    bl_idname = ADDON_ID

    custom_color_nodes: PointerProperty(type=CustomColorNodesSettings)
    round_values: PointerProperty(type=RoundValuesSettings)

    def draw(self, context):
        layout = self.layout

        if not _sections:
            layout.label(text="No tool has preferences yet.")
            return

        for owner, (title, draw_fn) in sorted(
            _sections.items(), key=lambda item: item[1][0].lower()
        ):
            header, body = layout.panel(f"eterea_prefs_{owner}", default_closed=True)
            header.label(text=title)
            if body is None:
                continue
            try:
                draw_fn(body, context)
            except Exception as exc:
                # A broken section must never make the whole Preferences
                # editor unusable.
                body.label(text=f"Error drawing section: {exc}", icon='ERROR')


classes = (
    *TOOL_SETTINGS,
    EtereaPreferences,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
