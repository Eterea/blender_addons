"""Generate the documentation icons of Eterea Blender Tools.

Every icon is defined here as SVG code, written to this folder as <tool>.svg and
rendered to PNG in two sizes. See ../ICON_STYLE.md for the visual rules.

Usage:  python3 build_icons.py   (requires: pip install cairosvg)
"""
import math, os

# ---- Palette -------------------------------------------------------------
TILE      = "#2B2B2B"   # tile background
TILE_EDGE = "#3D3D3D"   # subtle inner border of the tile
G_LIGHT   = "#E3E3E3"   # main lines / primary shapes
G_MID     = "#A3A3A3"   # secondary lines
G_DARK    = "#6E6E6E"   # tertiary lines, inactive parts
G_FILL    = "#484848"   # neutral filled surfaces
G_FILL2   = "#3A3A3A"   # deeper surfaces (stacked layers)
ORANGE    = "#FFA31A"   # key accent
ORANGE_D  = "#C2740A"   # darker orange (secondary accent / shade)
BLUE      = "#4C9BF0"   # second accent
BLUE_D    = "#2F64A8"   # darker blue

SIZE = 256
RADIUS = 25.6           # 10 % of the side


def tile():
    return (f'<rect x="0" y="0" width="{SIZE}" height="{SIZE}" rx="{RADIUS}" fill="{TILE}"/>'
            f'<rect x="2" y="2" width="{SIZE-4}" height="{SIZE-4}" rx="{RADIUS-2}" '
            f'fill="none" stroke="{TILE_EDGE}" stroke-width="4"/>')


def svg(body, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{SIZE}" height="{SIZE}" '
            f'viewBox="0 0 {SIZE} {SIZE}">'
            + (f"<defs>{defs}</defs>" if defs else "")
            + tile() + body + "</svg>\n")


def arrow(x1, y1, x2, y2, color, w=10, head=22):
    """Straight arrow with a solid triangular head ending at (x2, y2)."""
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy); ux, uy = dx / L, dy / L
    bx, by = x2 - ux * head, y2 - uy * head          # base of the head
    px, py = -uy * head * 0.6, ux * head * 0.6
    return (f'<line x1="{x1}" y1="{y1}" x2="{bx+ux*2:.1f}" y2="{by+uy*2:.1f}" stroke="{color}" '
            f'stroke-width="{w}" stroke-linecap="round"/>'
            f'<polygon points="{x2},{y2} {bx+px:.1f},{by+py:.1f} {bx-px:.1f},{by-py:.1f}" '
            f'fill="{color}" stroke="{color}" stroke-width="4" stroke-linejoin="round"/>')


def arc_arrow(cx, cy, r, a0, a1, color, w=12, head=26):
    """Circular arrow from angle a0 to a1 (degrees, clockwise screen coords)."""
    p = lambda a: (cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
    sweep = 1 if a1 > a0 else 0
    large = 1 if abs(a1 - a0) > 180 else 0
    # stop the line a bit before the tip so the head covers it
    sgn = 1 if a1 > a0 else -1
    a_stop = a1 - sgn * math.degrees(head * 0.8 / r)
    x0, y0 = p(a0); xs, ys = p(a_stop); xt, yt = p(a1)
    # tangent direction at the tip
    tx, ty = -math.sin(math.radians(a1)) * sgn, math.cos(math.radians(a1)) * sgn
    bx, by = xt - tx * head, yt - ty * head
    nx, ny = -ty * head * 0.6, tx * head * 0.6
    return (f'<path d="M{x0:.1f},{y0:.1f} A{r},{r} 0 {large} {sweep} {xs:.1f},{ys:.1f}" fill="none" '
            f'stroke="{color}" stroke-width="{w}" stroke-linecap="round"/>'
            f'<polygon points="{xt:.1f},{yt:.1f} {bx+nx:.1f},{by+ny:.1f} {bx-nx:.1f},{by-ny:.1f}" '
            f'fill="{color}" stroke="{color}" stroke-width="4" stroke-linejoin="round"/>')


def minus_badge(cx, cy, r=30):
    """Orange 'remove' badge with a knockout ring in the tile color."""
    return (f'<circle cx="{cx}" cy="{cy}" r="{r+8}" fill="{TILE}"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{ORANGE}"/>'
            f'<line x1="{cx-r*0.5}" y1="{cy}" x2="{cx+r*0.5}" y2="{cy}" stroke="{TILE}" '
            f'stroke-width="10" stroke-linecap="round"/>')


def sds_motif(x0, y0, s, circle_fill=G_FILL, dots=G_LIGHT, cage=G_DARK):
    """Subdivision motif: square cage with vertex dots + smooth circle inside."""
    x1, y1 = x0 + s, y0 + s
    cx, cy, r = x0 + s / 2, y0 + s / 2, s * 0.40
    out = (f'<rect x="{x0}" y="{y0}" width="{s}" height="{s}" fill="none" stroke="{cage}" '
           f'stroke-width="6" stroke-dasharray="14 10" stroke-linejoin="round"/>'
           f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{circle_fill}" stroke="{G_LIGHT}" stroke-width="12"/>')
    for (x, y) in [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]:
        out += f'<circle cx="{x}" cy="{y}" r="9" fill="{dots}"/>'
    return out


def node(x0, y0, w, h, header, header_h=40, body=G_FILL):
    """Generic node box with a colored header."""
    r = 14
    return (f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" rx="{r}" fill="{body}"/>'
            f'<path d="M{x0},{y0+header_h} V{y0+r} A{r},{r} 0 0 1 {x0+r},{y0} H{x0+w-r} '
            f'A{r},{r} 0 0 1 {x0+w},{y0+r} V{y0+header_h} Z" fill="{header}"/>')


icons = {}

# 1 ---------------------------------------------------------------- Asset Import Buttons
seg = ""
xs = 44; segw = 39; gap = 4
for i in range(4):
    x = xs + i * (segw + gap)
    seg += f'<rect x="{x}" y="166" width="{segw}" height="38" fill="{BLUE if i == 1 else G_FILL}"/>'
icons["asset_import_buttons"] = svg(
    f'<polygon points="128,40 174,66 128,92 82,66" fill="{ORANGE}"/>'
    f'<polygon points="82,66 128,92 128,144 82,118" fill="{G_MID}"/>'
    f'<polygon points="128,92 174,66 174,118 128,144" fill="{G_DARK}"/>'
    f'<g clip-path="url(#segclip)">{seg}</g>',
    defs=f'<clipPath id="segclip"><rect x="44" y="166" width="168" height="38" rx="14"/></clipPath>')

# 2 ---------------------------------------------------------------- Batch Operate Attributes
cards = ""
for (x, y, fill) in [(96, 40, G_FILL2), (72, 68, "#424242"), (44, 96, "#525252")]:
    cards += (f'<rect x="{x}" y="{y}" width="120" height="120" rx="14" fill="{fill}" '
              f'stroke="{TILE}" stroke-width="8"/>')
rows = ""
for i, y in enumerate([126, 156, 186]):
    c = ORANGE if i == 1 else G_LIGHT
    rows += (f'<rect x="62" y="{y-7}" width="14" height="14" rx="3" fill="{c}"/>'
             f'<rect x="86" y="{y-6}" width="{64 if i != 1 else 64}" height="12" rx="6" fill="{c}"/>')
icons["batch_operate_attributes"] = svg(cards + rows)

# 3 ---------------------------------------------------------------- Change Color Space
def picture(sky, sun, mount_back, mount_front):
    return (f'<rect x="48" y="48" width="160" height="160" fill="{sky}"/>'
            f'<circle cx="160" cy="92" r="20" fill="{sun}"/>'
            f'<polygon points="48,208 48,170 96,122 140,166 160,148 208,196 208,208" fill="{mount_back}"/>'
            f'<polygon points="48,208 48,190 110,150 168,208" fill="{mount_front}"/>')
icons["change_color_space"] = svg(
    f'<g clip-path="url(#frame)">'
    f'<g clip-path="url(#tri_a)">{picture(BLUE_D, ORANGE, BLUE, G_LIGHT)}</g>'
    f'<g clip-path="url(#tri_b)">{picture("#555555", "#BDBDBD", "#7A7A7A", "#9A9A9A")}</g>'
    f'</g>'
    f'<line x1="208" y1="48" x2="48" y2="208" stroke="{TILE}" stroke-width="8"/>'
    f'<rect x="48" y="48" width="160" height="160" rx="16" fill="none" stroke="{G_LIGHT}" stroke-width="10"/>',
    defs=('<clipPath id="frame"><rect x="48" y="48" width="160" height="160" rx="16"/></clipPath>'
          '<clipPath id="tri_a"><polygon points="40,40 216,40 40,216"/></clipPath>'
          '<clipPath id="tri_b"><polygon points="216,40 216,216 40,216"/></clipPath>'))

# 4 ---------------------------------------------------------------- Change Selected SDS Levels
bars = ""
for i, (x, h) in enumerate([(172, 32), (190, 58), (208, 84)]):
    bars += f'<rect x="{x-7}" y="{212-h}" width="14" height="{h}" rx="4" fill="{ORANGE if i < 2 else G_DARK}"/>'
icons["change_selected_sds_levels"] = svg(sds_motif(44, 44, 108) + bars)

# 5 ---------------------------------------------------------------- Change SDS UV Smooth
grid = ""
for k in range(1, 4):
    v = 52 + k * 38
    grid += (f'<line x1="{v}" y1="52" x2="{v}" y2="204" stroke="{BLUE}" stroke-width="4" opacity="0.75"/>'
             f'<line x1="52" y1="{v}" x2="204" y2="{v}" stroke="{BLUE}" stroke-width="4" opacity="0.75"/>')
uv = (f'<rect x="52" y="52" width="152" height="152" fill="none" stroke="{BLUE}" stroke-width="6"/>'
      + grid +
      f'<circle cx="128" cy="128" r="58" fill="none" stroke="{TILE}" stroke-width="22"/>'
      f'<circle cx="128" cy="128" r="58" fill="none" stroke="{G_LIGHT}" stroke-width="12"/>')
for (x, y) in [(52, 52), (204, 52), (204, 204), (52, 204)]:
    uv += f'<circle cx="{x}" cy="{y}" r="16" fill="{TILE}"/><circle cx="{x}" cy="{y}" r="11" fill="{ORANGE}"/>'
icons["change_selected_sds_uv_smooth"] = svg(uv)

# 6 ---------------------------------------------------------------- Copy Viewport Color
icons["copy_viewport_color"] = svg(
    f'<rect x="40" y="84" width="80" height="80" rx="12" fill="{ORANGE}" stroke="{G_LIGHT}" stroke-width="8"/>'
    f'<rect x="160" y="44" width="54" height="54" rx="10" fill="{ORANGE}" stroke="{ORANGE_D}" stroke-width="6"/>'
    f'<rect x="160" y="150" width="54" height="54" rx="10" fill="{ORANGE}" stroke="{ORANGE_D}" stroke-width="6"/>'
    + arrow(130, 112, 156, 84, BLUE, w=10, head=20)
    + arrow(130, 136, 156, 164, BLUE, w=10, head=20))

# 7 ---------------------------------------------------------------- Custom Color Nodes
sw = ""
cols = [G_MID, ORANGE, BLUE, ORANGE_D, BLUE_D]
for i, c in enumerate(cols):
    x = 48 + i * 33
    sw += f'<rect x="{x}" y="172" width="28" height="32" rx="6" fill="{c}"/>'
sw += f'<rect x="77" y="168" width="36" height="40" rx="9" fill="none" stroke="{G_LIGHT}" stroke-width="5"/>'
icons["custom_color_nodes"] = svg(
    node(48, 40, 160, 108, ORANGE)
    + f'<rect x="66" y="100" width="70" height="10" rx="5" fill="{G_MID}"/>'
    + f'<rect x="120" y="124" width="70" height="10" rx="5" fill="{G_MID}"/>'
    + f'<circle cx="48" cy="105" r="10" fill="{BLUE}" stroke="{TILE}" stroke-width="5"/>'
    + f'<circle cx="208" cy="129" r="10" fill="{G_LIGHT}" stroke="{TILE}" stroke-width="5"/>'
    + sw)

# 8 ---------------------------------------------------------------- Join Equalizing Bevels
c = 20
poly = [(40 + c, 112), (112, 112), (112, 64 + c), (112 + c, 64), (216 - c, 64), (216, 64 + c),
        (216, 192 - c), (216 - c, 192), (40 + c, 192), (40, 192 - c), (40, 112 + c)]
pts = " ".join(f"{x},{y}" for x, y in poly)
chamfers = [((112, 64 + c), (112 + c, 64)), ((216 - c, 64), (216, 64 + c)),
            ((216, 192 - c), (216 - c, 192)), ((40 + c, 192), (40, 192 - c)), ((40, 112 + c), (40 + c, 112))]
ch = "".join(f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}" stroke="{ORANGE}" '
             f'stroke-width="12" stroke-linecap="round"/>' for a, b in chamfers)
icons["join_equalizing_bevels"] = svg(
    f'<polygon points="{pts}" fill="{G_FILL}" stroke="{G_LIGHT}" stroke-width="8" stroke-linejoin="round"/>'
    f'<line x1="112" y1="120" x2="112" y2="184" stroke="{BLUE}" stroke-width="6" stroke-dasharray="10 8"/>'
    + ch)

# 9 ---------------------------------------------------------------- Remove Custom Label
icons["remove_custom_label"] = svg(
    node(40, 48, 156, 136, G_MID, header_h=46)
    + f'<rect x="58" y="62" width="90" height="18" rx="9" fill="{TILE}" opacity="0.55"/>'
    + f'<rect x="58" y="114" width="86" height="10" rx="5" fill="{G_DARK}"/>'
    + f'<rect x="58" y="140" width="60" height="10" rx="5" fill="{G_DARK}"/>'
    + f'<circle cx="40" cy="119" r="10" fill="{G_LIGHT}" stroke="{TILE}" stroke-width="5"/>'
    + f'<circle cx="196" cy="145" r="10" fill="{G_LIGHT}" stroke="{TILE}" stroke-width="5"/>'
    + minus_badge(184, 76, 28))

# 10 --------------------------------------------------------------- Remove Subdivision Modifiers
icons["remove_subdivision_modifiers"] = svg(sds_motif(44, 44, 128) + minus_badge(180, 180, 30))

# 11 --------------------------------------------------------------- Reset Active Modifier
hx, hy, hr = 148, 108, 32
# open-end wrench: handle + round head, jaw cut with the tile color (no masks: robust at any size)
icons["reset_active_modifier"] = svg(
    f'<line x1="{hx}" y1="{hy}" x2="94" y2="162" stroke="{G_LIGHT}" stroke-width="26" stroke-linecap="round"/>'
    f'<circle cx="{hx}" cy="{hy}" r="{hr}" fill="{G_LIGHT}"/>'
    f'<rect x="{hx-12}" y="{hy-52}" width="24" height="50" rx="4" fill="{TILE}" '
    f'transform="rotate(45 {hx} {hy})"/>'
    + arc_arrow(128, 128, 90, 160, -110, ORANGE, w=12, head=28))

# 12 --------------------------------------------------------------- Round Values
ticks = ""
for x, tall in [(56, False), (92, False), (128, True), (164, False), (200, False)]:
    h = 28 if tall else 14
    ticks += (f'<line x1="{x}" y1="{164-h}" x2="{x}" y2="{164+h}" stroke="{G_LIGHT if tall else G_DARK}" '
              f'stroke-width="{9 if tall else 6}" stroke-linecap="round"/>')
icons["round_values"] = svg(
    f'<line x1="40" y1="164" x2="216" y2="164" stroke="{G_DARK}" stroke-width="6" stroke-linecap="round"/>'
    + ticks
    + f'<circle cx="92" cy="70" r="17" fill="none" stroke="{BLUE}" stroke-width="8"/>'
    + f'<path d="M108,82 Q128,96 128,116" fill="none" stroke="{BLUE}" stroke-width="8" stroke-linecap="round"/>'
    + f'<polygon points="128,132 117,112 139,112" fill="{BLUE}" stroke="{BLUE}" stroke-width="4" stroke-linejoin="round"/>'
    + f'<circle cx="128" cy="164" r="19" fill="{ORANGE}" stroke="{TILE}" stroke-width="6"/>')

# 13 --------------------------------------------------------------- Set Curve Radius to 1.0
pts = [(60, 172), (128, 128), (196, 84)]
cr = (f'<path d="M60,172 C108,172 148,84 196,84" fill="none" stroke="{G_LIGHT}" stroke-width="10" '
      f'stroke-linecap="round"/>')
for (x, y) in pts:
    cr += (f'<circle cx="{x}" cy="{y}" r="24" fill="none" stroke="{TILE}" stroke-width="14"/>'
           f'<circle cx="{x}" cy="{y}" r="24" fill="none" stroke="{ORANGE}" stroke-width="7"/>'
           f'<circle cx="{x}" cy="{y}" r="8" fill="{G_LIGHT}"/>')
icons["set_curve_radius_to_1"] = svg(cr)

# 14 --------------------------------------------------------------- Toggle Lock Channels
def padlock(cx, body, closed):
    x0, y0 = cx - 34, 124
    if closed:
        sh = f'M{cx-20},{y0} V102 A20,20 0 0 1 {cx+20},102 V{y0}'
    else:
        sh = f'M{cx-20},{y0} V84 A20,20 0 0 1 {cx+20},84 V96'
    return (f'<path d="{sh}" fill="none" stroke="{G_LIGHT}" stroke-width="12" stroke-linecap="round"/>'
            f'<rect x="{x0}" y="{y0}" width="68" height="62" rx="12" fill="{body}"/>'
            f'<circle cx="{cx}" cy="{y0+26}" r="8" fill="{TILE}"/>'
            f'<rect x="{cx-4}" y="{y0+28}" width="8" height="18" rx="3" fill="{TILE}"/>')
icons["toggle_lock_transform_channels"] = svg(padlock(84, ORANGE, True) + padlock(172, G_MID, False))

# 15 --------------------------------------------------------------- Transform and Deltas
def cross(cx, cy, a):
    out = ""
    for (dx, dy) in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        out += arrow(cx, cy, cx + dx * a, cy + dy * a, G_LIGHT, w=9, head=17)
    return out
icons["transforms_deltas"] = svg(
    cross(80, 128, 42)
    + f'<polygon points="176,94 212,158 140,158" fill="none" stroke="{ORANGE}" stroke-width="12" '
      f'stroke-linejoin="round"/>'
    + f'<path d="M86,70 Q128,42 168,72" fill="none" stroke="{BLUE}" stroke-width="8" stroke-linecap="round"/>'
    + f'<polygon points="176,80 156,76 170,60" fill="{BLUE}" stroke="{BLUE}" stroke-width="3" stroke-linejoin="round"/>'
    + f'<path d="M170,190 Q128,218 88,188" fill="none" stroke="{BLUE}" stroke-width="8" stroke-linecap="round"/>'
    + f'<polygon points="80,180 100,184 86,200" fill="{BLUE}" stroke="{BLUE}" stroke-width="3" stroke-linejoin="round"/>')

# 16 --------------------------------------------------------------- Weight Ramp by Order
def mix(c1, c2, t):
    a = [int(c1[i:i+2], 16) for i in (1, 3, 5)]; b = [int(c2[i:i+2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(a[i] + (b[i]-a[i]) * t):02X}" for i in range(3))
vp = [(48, 172), (88, 104), (132, 150), (170, 82), (208, 58)]
wr = (f'<polyline points="{" ".join(f"{x},{y}" for x, y in vp)}" fill="none" stroke="url(#wg)" '
      f'stroke-width="9" stroke-linejoin="round" stroke-linecap="round"/>')
for i, (x, y) in enumerate(vp):
    wr += (f'<circle cx="{x}" cy="{y}" r="19" fill="{TILE}"/>'
           f'<circle cx="{x}" cy="{y}" r="13" fill="{mix(BLUE, ORANGE, i/4)}"/>')
wr += f'<rect x="48" y="198" width="160" height="12" rx="6" fill="url(#wg)"/>'
icons["create_weight_ramp"] = svg(
    wr, defs=(f'<linearGradient id="wg" x1="48" y1="0" x2="208" y2="0" gradientUnits="userSpaceOnUse">'
              f'<stop offset="0" stop-color="{BLUE}"/><stop offset="1" stop-color="{ORANGE}"/></linearGradient>'))

# ---- Output ---------------------------------------------------------------
# Folder layout (relative to this script, which lives in etr_blender_tools/icons/src/):
#   etr_blender_tools/icons/src/<tool>.svg   vector sources (256 x 256)
#   etr_blender_tools/icons/<tool>.png       large icons, 256 px (full documentation README)
#   icons/<tool>.png                          small icons, 64 px (repository README table)
HERE = os.path.dirname(os.path.abspath(__file__))
LARGE_DIR = os.path.normpath(os.path.join(HERE, ".."))
SMALL_DIR = os.path.normpath(os.path.join(HERE, "..", "..", "..", "icons"))
LARGE_PX, SMALL_PX = 256, 64

if __name__ == "__main__":
    import cairosvg  # pip install cairosvg
    os.makedirs(SMALL_DIR, exist_ok=True)
    for name, data in icons.items():
        svg_path = os.path.join(HERE, f"{name}.svg")
        with open(svg_path, "w") as f:
            f.write(data)
        # Both sizes are rendered from the vector source, so the small ones stay crisp.
        cairosvg.svg2png(url=svg_path, write_to=os.path.join(LARGE_DIR, f"{name}.png"),
                         output_width=LARGE_PX, output_height=LARGE_PX)
        cairosvg.svg2png(url=svg_path, write_to=os.path.join(SMALL_DIR, f"{name}.png"),
                         output_width=SMALL_PX, output_height=SMALL_PX)
    print(f"{len(icons)} icons written")
