# Eterea Blender Add-ons

Free tools for Blender by [Eterea Estudios](https://www.etereaestudios.com), bundled into a single **Blender Extension**: **Eterea Blender Tools**.

![Blender](https://img.shields.io/badge/Blender-5.2%2B-orange) ![License](https://img.shields.io/badge/license-GPL--3.0--or--later-blue)

## Download and install

1. Go to the [**Releases**](../../releases/latest) page and download `etr_blender_tools-<version>.zip`.
2. In Blender: `Edit > Preferences > Get Extensions > ⌄ (top-right menu) > Install from Disk...`
3. Select the downloaded `.zip` and enable the extension if it is not enabled automatically.

To update, install the new `.zip` the same way: it replaces the previous version.

**Requires Blender 5.2 or newer.**

## What is included

| Tool | Where to find it |
| --- | --- |
| Asset Import Buttons | Asset Browser header |
| Batch Operate Attributes | Right-click › Eterea Tools (3D Viewport, Outliner) |
| Change Color Space | Right-click › Eterea Tools (Shader Editor) |
| Change Selected SDS Levels | Sidebar › Eterea Tools › Subdivision |
| Change SDS UV Smooth | Sidebar › Eterea Tools › Subdivision |
| Copy Viewport Color | Object › Link/Transfer Data |
| Custom Color Nodes | Node Editors › Sidebar › Node, or the `D` key |
| Join Equalizing Bevels | Sidebar › Eterea Tools |
| Remove Custom Label from Selected Nodes | Right-click › Eterea Tools (Node Editors) |
| Remove Subdivision Modifiers | Sidebar › Eterea Tools › Subdivision |
| Reset Active Modifier to Defaults | Sidebar › Eterea Tools, and modifier right-click menu |
| Round Values | Object › Transform, and Right-click › Eterea Tools |
| Set Curve Radius to 1.0 | Right-click › Eterea Tools (Curve Edit Mode) |
| Toggle Lock Channels for Selected | Right-click › Eterea Tools (3D Viewport, Outliner) |
| Transform and Deltas | Properties › Object › Transform |
| Weight Ramp by Order | Sidebar › Eterea Tools |

Full documentation of every tool: [etr_blender_tools/README.md](etr_blender_tools/README.md)  
Version history: [etr_blender_tools/CHANGELOG.md](etr_blender_tools/CHANGELOG.md)

## Repository structure

```
etr_blender_tools/   Source code of the extension (one .py module per tool)
LICENSE              GNU General Public License v3.0
```

To build the installable `.zip` from the source:

```
blender --command extension build --source-dir etr_blender_tools
```

## Feedback and issues

Found a bug or have an idea? Please open an [issue](../../issues).

## More resources

More Blender resources, courses and tools: [etereaestudios.com/resources/blender-resources](https://etereaestudios.com/resources/blender-resources/)

## License

Released under the [GNU General Public License v3.0 or later](LICENSE).  
© 2026 Cristobal Vila ([etereaestudios.com](https://www.etereaestudios.com)).
