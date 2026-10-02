# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Cristobal Vila (etereaestudios.com)

"""
Asset Import Buttons

Adds a compact row of icon-only toggle buttons at the start of the Asset Browser
header (so they stay visible even in narrow editors), one per Import Method
(Follow Asset or Preferences, Link, Append, Pack).

The buttons are bound to the very same property used by Blender's native
"Import Settings" popover (space_data.params.import_method), so:
  - The native popover is left untouched and keeps working.
  - Both controls are always in sync (changing one updates the other).
  - The active method is highlighted with the theme's standard "pressed" color.

Robustness notes:
  - Buttons are prepended to the header (never replacing Blender's own draw code).
  - They only appear in Asset Browser mode, never in the regular File Browser.
  - They are hidden for the libraries where Blender hides "Import Settings"
    (Current File / Essentials), since nothing is imported there.
  - The setting is per editor: each Asset Browser shows and edits its own value.
  - Available methods and their icons are read at runtime from Blender's RNA,
    so the add-on adapts to new/renamed/removed methods across versions.
  - Any drawing error is swallowed so the native header can never break.
"""

bl_info = {
    "name": "Asset Import Buttons",
    "author": "Idea by Cristobal Vila / Code by Claude.ai",
    "version": (1, 0, 2),
    "blender": (5, 2, 0),
    "location": "Asset Browser > Header (left side)",
    "description": (
        "Icon-only buttons in the Asset Browser header to see and change the "
        "Import Method (Follow Preferences, Link, Append, Pack) at a glance."
    ),
    "category": "User Interface",
}

import bpy


# Import method identifiers that should never get a button.
# 'APPEND_REUSE' exists in some Blender versions but is not shown in the
# Blender 5.2 menu; skipping it keeps the row to the 4 expected buttons.
SKIPPED_METHODS = {'APPEND_REUSE'}

# Text label used instead of an icon for specific methods.
# 'FOLLOW_PREFS' has no icon of its own, so a "P" (Preferences) is used.
TEXT_LABELS = {'FOLLOW_PREFS': "P"}

# Libraries where Blender's own header hides the "Import Settings" popover.
LIBRARIES_WITHOUT_IMPORT = {'LOCAL', 'ESSENTIALS'}

# Set after the first drawing error, so the console gets one message instead
# of one per redraw.
_error_reported = False


def _get_asset_params(context):
    """Return the Asset Browser params if the buttons should be drawn, else None."""
    space = context.space_data
    if space is None or space.type != 'FILE_BROWSER':
        return None
    if getattr(space, "browse_mode", None) != 'ASSETS':
        return None

    params = space.params
    if params is None or not hasattr(params, "import_method"):
        return None

    library = getattr(params, "asset_library_reference", None)
    if library in LIBRARIES_WITHOUT_IMPORT:
        return None

    return params


def _iter_import_methods(params):
    """Yield (identifier, name, icon) for every import method Blender currently offers."""
    prop = params.bl_rna.properties["import_method"]
    for item in prop.enum_items:
        if item.identifier in SKIPPED_METHODS:
            continue
        yield item.identifier, item.name, item.icon


def draw_import_method_buttons(self, context):
    """Header draw callback prepended to FILEBROWSER_HT_header."""
    try:
        params = _get_asset_params(context)
        if params is None:
            return

        layout = self.layout

        row = layout.row(align=True)
        for identifier, name, icon in _iter_import_methods(params):
            label = TEXT_LABELS.get(identifier)

            if label is None and icon != 'NONE':
                # Icon-only square button; the tooltip shows the method's description.
                row.prop_enum(params, "import_method", identifier, text="", icon=icon)
            else:
                # Letter button forced to the same square width as icon buttons.
                sub = row.row(align=True)
                sub.ui_units_x = 1.0
                sub.prop_enum(params, "import_method", identifier,
                              text=label or name[:1])

        # Gap between the buttons and the native header items that follow.
        layout.separator()
    except Exception as exc:  # Never let an add-on error break the native header.
        global _error_reported
        if not _error_reported:
            _error_reported = True
            print(f"[etr_blender_tools] asset_import_buttons draw error: {exc}")


def register():
    bpy.types.FILEBROWSER_HT_header.prepend(draw_import_method_buttons)


def unregister():
    bpy.types.FILEBROWSER_HT_header.remove(draw_import_method_buttons)
