# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Cristobal Vila (etereaestudios.com)

"""
Eterea Documentation (shared infrastructure, not a tool by itself)

Links to the online documentation of the kit. The documentation is not part of
the installed Extension: it lives on GitHub, in the "etr_blender_tools_docs"
folder of the repository.

  - "Manual" row at the top of the kit's section of the Preferences
    (Preferences > Add-ons > Eterea Blender Tools). It mimics the native
    "Website" row that Blender draws above it from the manifest. See
    draw_manual_row(), called by preferences.py.
  - "Open Online Readme" button at the bottom of the "Eterea Tools" tab of the
    3D Viewport Sidebar (N).

Both open DOCUMENTATION_URL in the web browser using Blender's own
wm.url_open operator, so this module defines no operators.

This module is registered last (see MODULES in __init__.py) so that its Sidebar
panel is the last one of the Eterea Tools tab; bl_order reinforces it.
"""

import bpy

from . import eterea_ui

# Full manual on GitHub (rendered Markdown).
DOCUMENTATION_URL = (
    "https://github.com/Eterea/blender_addons/blob/main/etr_blender_tools_docs/README.md"
)

BUTTON_LABEL = "Open Online Readme"


def draw_readme_button(layout):
    """Draw the "Open Online Readme" button."""
    layout.operator("wm.url_open", text=BUTTON_LABEL, icon='HELP').url = DOCUMENTATION_URL


def draw_manual_row(layout):
    """Draw a "Manual | Open Online Readme" row, laid out like the native
    "Website" row of the Preferences (right-aligned label, half-width button)."""
    split = layout.split(factor=0.15)
    col_label = split.column()
    col_button = split.column()
    col_label.alignment = 'RIGHT'
    col_label.label(text="Manual")
    draw_readme_button(col_button.split(factor=0.5))


class ETR_PT_documentation(bpy.types.Panel):
    """Last panel of the Eterea Tools tab in the 3D Viewport Sidebar (N)"""
    bl_label = "Documentation"
    bl_idname = "ETR_PT_documentation"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = eterea_ui.SIDEBAR_CATEGORY
    bl_order = 1000
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        draw_readme_button(self.layout)


classes = (
    ETR_PT_documentation,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
