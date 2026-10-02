# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Cristobal Vila (etereaestudios.com)

"""etr_blender_tools - Eterea Blender Tools

Blender Extension that bundles the whole set of Eterea tools into a single
install. Each tool lives in its own .py module (without the "etr_" prefix,
which here only identifies the kit as a whole). This __init__.py does not
implement anything: it just imports every module and calls its own
register() / unregister() functions.

Two modules are shared infrastructure, so they are always registered first
(and unregistered last):
  - eterea_ui:   the "Eterea Tools" Sidebar tab name and the "Eterea Tools"
                 right-click submenus.
  - preferences: the single AddonPreferences class of the kit, with one
                 collapsible section per tool that has preferences.

To add a new tool in the future:
  1. Copy its .py file into this same folder.
  2. Add its module name (without ".py") to the MODULES tuple below.
  3. If it needs the Sidebar tab or the right-click submenus, use eterea_ui
     (see the docstring of eterea_ui.py).
  4. If it needs its own preferences, see the docstring of preferences.py.
"""

import importlib
import traceback

# Module names (without the .py extension), in registration order.
# Shared infrastructure first, then the tools in alphabetical order.
MODULES = (
    "eterea_ui",
    "preferences",
    "asset_import_buttons",
    "batch_operate_attributes",
    "change_color_space",
    "change_selected_sds_levels",
    "change_selected_sds_uv_smooth",
    "copy_viewport_color",
    "create_weight_ramp",
    "custom_color_nodes",
    "join_equalizing_bevels",
    "remove_custom_label",
    "remove_subdivision_modifiers",
    "reset_active_modifier",
    "round_values",
    "set_curve_radius_to_1",
    "toggle_lock_transform_channels",
    "transforms_deltas",
)

_submodules = []


def _report_error(action, name):
    """Print a kit error with its full traceback, so it can be diagnosed."""
    print(f"[etr_blender_tools] Error {action} '{name}':")
    traceback.print_exc()


def _import_submodules():
    """Import every module listed in MODULES, in order.

    A module that fails to import (syntax error, missing dependency...) is
    reported and skipped, so it never prevents the rest of the kit from
    loading.
    """
    _submodules.clear()
    for name in MODULES:
        try:
            module = importlib.import_module(f".{name}", __name__)
        except Exception:
            _report_error("importing", name)
            continue
        _submodules.append(module)


def register():
    _import_submodules()
    for module in _submodules:
        try:
            module.register()
        except Exception:
            # A failure in one tool must not prevent the rest of the kit from
            # loading; it is reported in the console so it can be diagnosed.
            _report_error("registering", module.__name__)


def unregister():
    # Unregister in reverse order, as usual.
    for module in reversed(_submodules):
        try:
            module.unregister()
        except Exception:
            _report_error("unregistering", module.__name__)
