# Icon style guide — Eterea Blender Tools documentation

These icons illustrate the online documentation of the kit (the two README files).
**They are not used by the add-ons' interface inside Blender.**

Use this guide when a new tool is added to the kit, so its icon matches the rest.

---

## Files and folders

| What | Where | Size |
| --- | --- | --- |
| Vector sources | `etr_blender_tools_docs/icons/src/<tool>.svg` | 256 × 256 |
| Generator script | `etr_blender_tools_docs/icons/src/build_icons.py` | — |
| Large icons (full documentation README) | `etr_blender_tools_docs/icons/<tool>.png` | 256 px, shown at 64 px |
| Small icons (repository README table) | `icons/<tool>.png` | 64 px, shown at 32 px |

- The file name is the **module name of the tool** (`round_values.py` → `round_values.png`).
- Both PNG sizes are rendered **from the vector source** (not by downscaling the large PNG), so the small ones stay crisp.
- PNG files are shown at half their real size in the READMEs, so they look sharp on high-density (Retina) screens.
- The documentation folder (`etr_blender_tools_docs/`) lives outside the extension folder (`etr_blender_tools/`), so none of these files ends up in the installable `.zip`.

### Regenerating the icons

All icons are defined as SVG code inside `build_icons.py`, one block per tool, using shared helpers and the palette constants. To add or change an icon, edit that file and run:

```
pip install cairosvg
python3 etr_blender_tools_docs/icons/src/build_icons.py
```

It rewrites the `.svg` sources and both PNG sets.

### Using them in the READMEs

Repository README (`README.md`, "What is included" table), first column:

```html
<img src="icons/<tool>.png" width="32" alt="">
```

Full documentation (`etr_blender_tools_docs/README.md`), inside the tool heading:

```markdown
### <img src="icons/<tool>.png" width="64" alt=""> Tool Name
```

---

## Visual rules

### Format

- Square canvas of **256 × 256** (design grid in px at that size).
- A **tile** fills the whole canvas: rounded square with a corner radius of **25.6 px (10 % of the side)**.
- Everything outside the tile is **transparent**, so the rounded corners work on light and dark backgrounds.
- The tile has a subtle **4 px inner border** (`#3D3D3D`) that separates it from very dark backgrounds.
- Keep the drawing inside a **safe area of 40–216 px** (40 px margin on every side).

### Character

- **Flat** graphic design, like the icons of a user interface: solid fills and strokes only.
- **No** gradients for shading, no shadows, no glows, no 3D lighting, no textures. (The only gradient allowed is a meaningful one, such as the blue → orange ramp of *Weight Ramp by Order*.)
- **No text**: letters do not survive at 32 px. Use shapes and symbols instead.
- One simple idea per icon, made of 2–4 elements. If the tool's action is abstract, use a symbol (a padlock, a wrench, a delta triangle) rather than a scene.
- Round line caps and round joins (`stroke-linecap="round"`, `stroke-linejoin="round"`).

### Palette

Greys dominate; the two accents highlight the key part of each icon.

| Role | Color | Use |
| --- | --- | --- |
| Tile background | `#2B2B2B` | The rounded square (Blender-like dark UI grey) |
| Tile border | `#3D3D3D` | 4 px inner border of the tile |
| Light grey | `#E3E3E3` | Main lines and primary shapes |
| Mid grey | `#A3A3A3` | Secondary lines and shapes |
| Dark grey | `#6E6E6E` | Tertiary lines, inactive or "before" parts, cages |
| Fill grey | `#484848` | Neutral filled surfaces (node bodies, mesh faces) |
| Deep fill grey | `#3A3A3A` | Surfaces further back (stacked layers) |
| **Orange** (key accent) | `#FFA31A` | The thing the tool changes or produces; the result |
| Dark orange | `#C2740A` | Secondary orange (outlines of selected items, darker swatches) |
| **Blue** (second accent) | `#4C9BF0` | Actions and relationships: arrows, active toggles, guides, "before" state |
| Dark blue | `#2F64A8` | Secondary blue (backgrounds inside an image, darker swatches) |

Guideline: **orange = what changes / the result, blue = the action or the link between things.** Each icon uses orange, and blue only when it helps. Avoid any other hue.

### Line weights (at 256 px)

| Weight | Use |
| --- | --- |
| 12 px | Main strokes (circles, outlines that carry the idea, circular arrows) |
| 8–10 px | Secondary strokes, arrows |
| 6 px | Fine details: cages, dashed lines, ticks |

At 64 px these become 3 / 2–2.5 / 1.5 px, so nothing thinner than 6 px should be used.

### Knockout outline

When two shapes overlap, the one in front gets an extra outline in the **tile color** (`#2B2B2B`, 5–8 px) so they read as separate shapes without adding lines. Example: the stacked cards of *Batch Operate Attributes*, the vertex dots of *Weight Ramp by Order*.

### Recurring motifs (the visual vocabulary of the kit)

| Motif | Meaning | Used in |
| --- | --- | --- |
| Dashed dark-grey square with light vertex dots + light circle inside | Subdivision Surface | Change Selected SDS Levels, Change SDS UV Smooth, Remove Subdivision Modifiers |
| Orange circle with a dark minus, with a knockout ring | Remove / clear | Remove Subdivision Modifiers, Remove Custom Label |
| Rounded box with a colored header, body lines and side socket dots | Node | Custom Color Nodes, Remove Custom Label |
| Orange circular arrow (counter-clockwise) | Reset to defaults | Reset Active Modifier to Defaults |
| Blue straight or curved arrow | Copy / move / transfer | Copy Viewport Color, Transform and Deltas, Round Values |
| Blue → orange | From first to last / from before to after | Weight Ramp by Order, Round Values |
| Blue segment in a row of grey segments | Active toggle button (as in Blender's UI) | Asset Import Buttons |

Reuse these motifs before inventing new ones, so the family stays consistent.

---

## Current icons

| Tool | Concept |
| --- | --- |
| Asset Import Buttons | Isometric cube (asset, orange top) over a 4-segment toggle bar with one active blue segment |
| Batch Operate Attributes | Three stacked cards (many objects); the front one shows an attribute list with one orange row |
| Change Color Space | Image split diagonally: one half in color (blue / orange), the other half in greys |
| Change Selected SDS Levels | Subdivision motif + ascending level bars (two orange, one grey) |
| Change SDS UV Smooth | Subdivision circle over a blue UV grid, with orange corner points (Keep Corners / Boundaries) |
| Copy Viewport Color | Active orange square with light outline; blue arrows to two selected squares that turn orange |
| Custom Color Nodes | Node with an orange header over a row of color swatches, one selected |
| Join Equalizing Bevels | Two joined shapes (blue dashed seam) whose chamfered corners are all the same orange size |
| Remove Custom Label from Selected Nodes | Node whose header label is emptied, with the orange minus badge |
| Remove Subdivision Modifiers | Subdivision motif + orange minus badge |
| Reset Active Modifier to Defaults | Light-grey wrench (modifier) inside an orange counter-clockwise arrow |
| Round Values | Blue off-grid point with an arrow snapping to an orange point exactly on the main tick |
| Set Curve Radius to 1.0 | Light curve with three control points, all with identical orange radius rings |
| Toggle Lock Channels for Selected | Closed orange padlock next to an open grey padlock |
| Transform and Deltas | Move arrows and an orange delta triangle, linked by two blue exchange arrows |
| Weight Ramp by Order | Path of vertices colored from blue (first) to orange (last), with a blue → orange ramp bar |

---

## Checklist for a new icon

1. Add a block to `build_icons.py`, named after the tool's module.
2. Start from an existing motif if one fits; otherwise pick one clear symbol.
3. Light grey for the main shape, orange for the result, blue for the action (only if needed).
4. Stay inside the 40–216 px safe area; minimum stroke 6 px; no text.
5. Run the script and check the 64 px PNG at 32 px on a white and on a near-black background: it must still be recognizable.
6. Add the icon to both READMEs and a row to the *Current icons* table above.
