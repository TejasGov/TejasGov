#!/usr/bin/env python3
"""Builds the static artwork used by README.md (the live activity panel is
built daily by build_activity.py in CI).

    pip install fonttools uharfbuzz numpy pillow
    python3 scripts/build_assets.py

Fonts (Instrument Serif, Geist, Geist Mono; all SIL OFL), icons (simple-icons,
CC0) and project screenshots are downloaded once into scripts/.cache/.
"""

import base64
import io
import math
import re

import numpy as np
from PIL import Image

import ascii3d as a3
from kit import (
    DIM, EMBER, FAINT, INK, INK_DEEP, LIGHT_ACCENT, LIGHT_MUTED, LIGHT_TEXT, LINE, MARIGOLD, MUTED,
    REDUCED_MOTION, SAFFRON, SOFT, TEXT, ascii_css, ascii_runs, document, fetch, font, num, panel,
    rng, text, wrap, write,
)

SERIF = font("serif")
SANS = font("sans", 400)
SANS_M = font("sans", 500)
MONO = font("mono", 400)
MONO_M = font("mono", 500)

# ASCII grid: 10px characters on a 6 × 10.5 px cell
FS, CW, CH = 10, 6.0, 10.5

# ── content ─────────────────────────────────────────────────────────────────
PROJECTS = [
    {
        "slug": "stratos",
        "name": "Stratos",
        "kind": "FLIGHT GAME",
        "desc": "An open-world fighter jet game for the browser, with physically based skies, "
                "volumetric storms and nine jets, from the wavetops to the edge of space.",
        "stack": ["Three.js", "WebGL 2", "Rapier", "TypeScript"],
        "art": ("photo", "https://raw.githubusercontent.com/TejasGov/Stratos/HEAD/docs/images/edge-of-space.jpg", 0.40),
        "caption": "FIG. 2  THE EDGE OF SPACE, IN ENGINE",
    },
    {
        "slug": "yudhveer",
        "name": "Yudhveer",
        "kind": "ACTION GAME",
        "desc": "An Indian mythological action game. Cel-shaded sword-and-shield combat across "
                "five worlds, with bosses that block and parry back.",
        "stack": ["Three.js", "Rapier", "TypeScript", "Vite"],
        "art": ("photo", "https://raw.githubusercontent.com/TejasGov/Yudhveer/HEAD/docs/media/08-summit-eclipse.jpg", 0.42),
        "caption": "FIG. 3  THE SUMMIT, UNDER ECLIPSE",
    },
    {
        "slug": "echoscribe",
        "name": "EchoScribe",
        "kind": "CLINICAL AI",
        "desc": "An ambient clinical scribe that turns doctor–patient conversations into "
                "structured, FHIR-ready SOAP notes in real time.",
        "stack": ["React", "FastAPI", "BioNLP", "FHIR R4"],
        "art": ("ridgeline",),
        "caption": "FIG. 4  A CONVERSATION, AS IT HAPPENS",
    },
    {
        "slug": "socra",
        "name": "Socra",
        "kind": "AI FOR EDUCATION",
        "desc": "A Socratic AI learning platform for UB's intro CS courses: guided hints, "
                "sandboxed code runs, adaptive practice and faculty analytics.",
        "stack": ["TypeScript", "Postgres", "Redis", "Docker"],
        "art": ("solid",),
        "caption": "FIG. 5  PLATO'S DODECAHEDRON, IN ASCII",
    },
]

TOOLKIT = [
    ("Languages", ["TypeScript", "JavaScript", "Python", "Java", "C", "HTML", "CSS"]),
    ("Frontend", ["React", "Next.js", "Vue", "Tailwind", "Three.js", "Framer Motion"]),
    ("Backend & cloud", ["Node.js", "Firebase", "MongoDB", "MySQL", "AWS", "Google Cloud", "Azure", "Kubernetes", "Vercel"]),
    ("ML & data", ["PyTorch", "TensorFlow", "scikit-learn", "OpenCV", "pandas"]),
    ("Design & games", ["Figma", "Premiere Pro", "Godot"]),
    ("AI tooling", ["Claude Code", "Lovable", "Antigravity", "OpenClaw"]),
]

LINKEDIN = ("M20.45 20.45h-3.56v-5.57c0-1.33-.02-3.04-1.85-3.04-1.85 0-2.14 1.45-2.14 2.94v5.67H9.35V9h3.41v1.56h.05"
            "c.48-.9 1.64-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 5.46v6.28zM5.34 7.43a2.06 2.06 0 1 1 0-4.13 2.06 2.06 0 0 1 0 4.13z"
            "M7.12 20.45H3.56V9h3.56v11.45z")
KEYS = [
    ("linkedin", "LinkedIn", LINKEDIN),
    ("email", "Email", "gmail"),
    ("youtube", "YouTube", "youtube"),
    ("instagram", "Instagram", "instagram"),
    ("kaggle", "Kaggle", "kaggle"),
    ("blog", "Blog", "wordpress"),
    ("x", "X", "x"),
    ("hackerrank", "HackerRank", "hackerrank"),
]
ACCENT_KEY = "email"

SECTIONS = [("about", "About"), ("work", "Selected work"), ("toolkit", "Toolkit"), ("activity", "Activity")]


# ── helpers ─────────────────────────────────────────────────────────────────
def simple_icon(name):
    raw = fetch(f"https://cdn.jsdelivr.net/npm/simple-icons@16.35.0/icons/{name}.svg", f"si-{name}.svg").read_text()
    return re.search(r'<path d="([^"]+)"', raw).group(1)


def strip(frames_svg, x, y, w, h, frame_h, seconds, cls):
    """Frames stacked vertically and rolled through a fixed window, one step per frame."""
    n = len(frames_svg)
    body = "".join(f'<g transform="translate(0 {num(i * frame_h)})">{f}</g>' for i, f in enumerate(frames_svg))
    css = (f".{cls}{{animation:{cls} {seconds}s steps({n}) infinite}}"
           f"@keyframes {cls}{{to{{transform:translateY({num(-n * frame_h)}px)}}}}")
    clip = f'<clipPath id="{cls}-win"><rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}"/></clipPath>'
    return clip, f'<g clip-path="url(#{cls}-win)"><g class="{cls}">{body}</g></g>', css


def cycle(layers, seconds, cls, order=None):
    """Hard-cut between layers in `order` (indices); the first layer is the still frame."""
    order = order or list(range(len(layers)))
    slot = 100 / len(order)
    css, out = [], []
    for i, layer in enumerate(layers):
        frames = [f"{num(k * slot)}%{{opacity:{1 if j == i else 0}}}" for k, j in enumerate(order)]
        frames.append(f"100%{{opacity:{1 if order[0] == i else 0}}}")
        css.append(f".{cls}{i}{{animation:{cls}{i} {seconds}s step-end infinite}}"
                   f"@keyframes {cls}{i}{{{''.join(frames)}}}")
        out.append(f'<g class="{cls}{i}"{"" if i == 0 else " opacity=\"0\""}>{layer}</g>')
    return "".join(out), "".join(css)


def ascii_stars(seed, w, h, count, avoid, twinkle=6):
    r = rng(seed)
    cols, rows = int(w / CW), int(h / CH)
    grid = [[None] * cols for _ in range(rows)]
    tw = []
    for i in range(count):
        c, rr = r.randrange(cols), r.randrange(rows)
        if any(x0 <= c * CW <= x1 and y0 <= rr * CH <= y1 for x0, y0, x1, y1 in avoid):
            continue
        ch = r.choice(".......'`+*")
        if i < twinkle:
            delay = r.uniform(0, 5)
            tw.append(f'<text class="tw" x="{num(c * CW)}" y="{num((rr + 1) * CH)}" '
                      f'style="animation-delay:-{delay:.1f}s">{r.choice("+*")}</text>')
        else:
            grid[rr][c] = (ch, "t0" if r.random() < 0.7 else "t1")
    return ascii_runs(grid, 0, CH, CW, CH) + f'<g class="t1">{"".join(tw)}</g>'


def photo_data_uri(url, slug, focus_y, w, h):
    src = fetch(url, f"shot-{slug}.jpg")
    im = Image.open(src).convert("RGB")
    target = w / h
    iw, ih = im.size
    if iw / ih > target:
        cw = int(ih * target)
        x0 = (iw - cw) // 2
        im = im.crop((x0, 0, x0 + cw, ih))
    else:
        chh = int(iw / target)
        y0 = int(max(0, min(ih - chh, focus_y * ih - chh / 2)))
        im = im.crop((0, y0, iw, y0 + chh))
    im = im.resize((int(w * 1.6), int(h * 1.6)), Image.LANCZOS)
    buffer = io.BytesIO()
    im.save(buffer, "JPEG", quality=80, optimize=True, progressive=True)
    return "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode()


# ── header ──────────────────────────────────────────────────────────────────
def header():
    W, H = 1200, 520
    cx, cy, R = 906, 262, 134
    x0 = 72

    # corona + limb: a still layer and two variants it flickers through
    rx0, cols, rows = 540, int(660 / CW) + 1, int(H / CH) + 1
    variants = []
    for k, drift in enumerate((0.0, 0.7, 1.4)):
        grid = a3.corona(cols, rows, CW, CH, cx - rx0, cy, R, drift=drift, sparkle=k)
        variants.append(ascii_runs(grid, rx0, CH * 0.78, CW, CH))
    corona_svg, corona_css = cycle(variants, 2.4, "cr", order=[0, 1, 2, 1])

    # the moon: 72 frames of one slow turn, earthshine only
    moon = a3.Moon()
    mc0 = math.floor((cx - R - rx0) / CW) - 1
    mr0 = math.floor((cy - R) / CH) - 1
    mcols = math.ceil(2 * R / CW) + 3
    mrows = math.ceil(2 * R / CH) + 3
    mx, my = rx0 + mc0 * CW, mr0 * CH
    frames = []
    n_frames = 48
    for i in range(n_frames):
        grid = a3.moon_frame(moon, 2 * math.pi * i / n_frames, mcols, mrows, CW, CH,
                             cx - mx, cy - my, R)
        frames.append(ascii_runs(grid, mx, my + CH * 0.78, CW, CH))
    chars = sum(1 for row in a3.moon_frame(moon, 0, mcols, mrows, CW, CH, cx - mx, cy - my, R) for c in row if c and c[0] != " ")
    clip, moon_svg, moon_css = strip(frames, mx, my, mcols * CW, mrows * CH, mrows * CH, 10.6, "mn")

    stars = ascii_stars(17, W, H, 70, avoid=[(0, 0, 640, H), (cx - 260, cy - 250, cx + 260, cy + 250)], twinkle=5)
    stars_left = ascii_stars(29, 640, H, 26, avoid=[(40, 70, 640, 480)], twinkle=2)

    # type
    name = (text(SERIF, "Tejas", 148, x0 - 6, 214, TEXT, track=-2)
            + text(SERIF, "Govind", 148, x0 - 6, 336, TEXT, track=-2))
    lines = wrap(SANS, "CS student at the University at Buffalo, building browser games, "
                       "real-time web apps and machine-learning experiments.", 19, 470)
    statement = "".join(text(SANS, line, 19, x0, 390 + i * 28, SOFT) for i, line in enumerate(lines))
    meta, mx_ = [], x0
    for i, label in enumerate(["FULL-STACK", "GAMES", "APPLIED ML"]):
        meta.append(text(MONO, label, 12, mx_, 474, MUTED, track=1.6))
        mx_ += MONO.width(label, 12, 1.6)
        if i < 2:
            meta.append(f'<rect x="{num(mx_ + 12)}" y="465" width="5" height="5" fill="{SAFFRON}"/>')
            mx_ += 29
    top = (text(MONO, "GITHUB.COM/TEJASGOV", 12, x0, 58, DIM, track=1.6)
           + text(MONO, "BUFFALO, NY  42.89° N  78.88° W", 12, W - 48, 58, DIM, anchor="end", track=1.6))
    caption = text(MONO, f"FIG. 1  ECLIPSE · {chars:,} CHARACTERS · {n_frames} FRAMES", 11, W - 48, H - 30,
                   DIM, anchor="end", track=1.4)

    defs, open_, close = panel(W, H, 26)
    body = (
        "<defs>" + defs + clip
        + f'<radialGradient id="warm" cx="{cx}" cy="{cy}" r="420" gradientUnits="userSpaceOnUse">'
          f'<stop offset="0" stop-color="#FF8A3D" stop-opacity=".10"/><stop offset="1" stop-color="#FF8A3D" stop-opacity="0"/></radialGradient>'
        + "</defs>"
        + open_
        + f'<rect width="{W}" height="{H}" fill="url(#warm)"/>'
        + f'<g class="a">{stars}{stars_left}{corona_svg}'
        + f'<circle cx="{cx}" cy="{cy}" r="{R * 0.995}" fill="{INK_DEEP}"/>'
        + moon_svg + "</g>"
        + top + name + statement + "".join(meta) + caption
        + close
    )
    css = (
        ascii_css(FS, {"m": "#5A6286", "l": MARIGOLD, "w": "#FFF4E2", "h": MARIGOLD, "s": SAFFRON, "e": "#D9703A", "d": "#7A4630",
                       "t0": FAINT, "t1": DIM})
        + ".tw{animation:tw 3.2s ease-in-out infinite alternate}@keyframes tw{from{opacity:.15}to{opacity:1}}"
        + moon_css + corona_css + REDUCED_MOTION
    )
    write("header.svg", document(W, H, "Tejas Govind. CS student at the University at Buffalo, building browser games, "
                                       "real-time web apps and machine-learning experiments.", body, css))


# ── keycaps ─────────────────────────────────────────────────────────────────
def keycap(slug, label, icon):
    W, H = 160, 168
    accent = slug == ACCENT_KEY
    if accent:
        skirt = ("#E07E2C", "#8C3F0E")
        top = ("#FFC47F", "#F79A45")
        rim, ink, sub = "#FFD9A8", "#2A1405", "#6B3410"
    else:
        skirt = ("#1D2140", "#0B0D1A")
        top = ("#272C52", "#1A1E3B")
        rim, ink, sub = "#3A4176", TEXT, MUTED
    path = icon if icon.startswith("M") else simple_icon(icon)
    body = (
        "<defs>"
        f'<linearGradient id="sk" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{skirt[0]}"/><stop offset="1" stop-color="{skirt[1]}"/></linearGradient>'
        f'<linearGradient id="tp" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{top[0]}"/><stop offset="1" stop-color="{top[1]}"/></linearGradient>'
        f'<radialGradient id="dish" cx=".5" cy=".38" r=".62"><stop offset="0" stop-color="#fff" stop-opacity="{".16" if accent else ".06"}"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>'
        '<filter id="sh" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="6"/></filter>'
        "</defs>"
        f'<rect x="16" y="26" width="128" height="134" rx="22" fill="#000" opacity=".45" filter="url(#sh)"/>'
        f'<rect x="8" y="8" width="144" height="148" rx="22" fill="url(#sk)"/>'
        f'<rect x="8.5" y="8.5" width="143" height="147" rx="21.5" fill="none" stroke="{rim}" stroke-opacity=".35"/>'
        f'<rect x="20" y="12" width="120" height="114" rx="16" fill="url(#tp)"/>'
        f'<rect x="20" y="12" width="120" height="114" rx="16" fill="url(#dish)"/>'
        f'<path d="M36 12.6h88" stroke="{rim}" stroke-opacity=".9" stroke-linecap="round"/>'
        f'<g transform="translate(64 34) scale(1.333)"><path fill="{ink}" d="{path}"/></g>'
        + text(MONO_M, label.upper(), 11.5, 80, 108, sub, anchor="middle", track=1.2)
    )
    write(f"keys/{slug}.svg", document(W, H, label, body))


# ── section titles (light + dark) ───────────────────────────────────────────
def section_titles():
    W, H = 1200, 92
    for slug, label in SECTIONS:
        for theme, fg, sub, accent, line in (("dark", TEXT, DIM, SAFFRON, LINE), ("light", LIGHT_TEXT, LIGHT_MUTED, LIGHT_ACCENT, "#D5D7E2")):
            lw = SERIF.width(label, 48, -0.6)
            path = f"~/{slug}"
            pw = MONO.width(path, 13, 1)
            body = (
                text(SERIF, label, 48, 0, 66, fg, track=-0.6)
                + f'<rect x="{num(lw + 24)}" y="53.5" width="{num(W - lw - 24 - pw - 20)}" height="1" fill="{line}"/>'
                + text(MONO, path, 13, W, 58, accent, anchor="end", track=1)
            )
            write(f"titles/{slug}-{theme}.svg", document(W, H, label, body))


# ── project art ─────────────────────────────────────────────────────────────
def ridgeline(x, y, w, h):
    """Stacked waveforms of a conversation that flows back into the distance."""
    r = np.random.default_rng(4)
    K, gap, pts = 22, 10, 64
    xs = np.linspace(x + 34, x + w - 34, pts)
    u = np.linspace(0, 1, pts)
    env = np.exp(-((u - 0.5) / 0.2) ** 2)
    lines = []
    for k in range(K):
        sig = np.zeros(pts)
        for _ in range(r.integers(3, 7)):
            c, s, a = r.uniform(0.3, 0.7), r.uniform(0.012, 0.05), r.uniform(0.3, 1.0)
            sig += a * np.exp(-((u - c) / s) ** 2)
        sig += r.normal(0, 0.05, pts)
        sig = np.abs(sig) * env + np.abs(r.normal(0, 0.012, pts))
        lines.append(np.clip(sig, 0, 1.6))
    paths = []
    xs = np.concatenate([[x - 20], xs, [x + w + 20]])
    for i in range(K * 2 + 8):
        base = y + 40 + i * gap
        ys = base - np.concatenate([[0], lines[i % K], [0]]) * 58
        d = "M" + " ".join(f"{a:.1f} {b:.1f}" for a, b in zip(xs, ys))
        paths.append(f'<path d="{d} {x + w + 20} {base + 60:.1f} {x - 20} {base + 60:.1f}Z"/>')
    css = (f".rl{{animation:rl 16s linear infinite}}@keyframes rl{{to{{transform:translateY({-K * gap}px)}}}}"
           ".rec{animation:rec 1.6s step-end infinite}@keyframes rec{50%{opacity:.2}}")
    defs = (f'<linearGradient id="fade" x1="0" y1="{y}" x2="0" y2="{y + h}" gradientUnits="userSpaceOnUse">'
            '<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".3" stop-color="#fff"/>'
            '<stop offset=".88" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
            f'<mask id="rm"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#fade)"/></mask>')
    art = (f'<g mask="url(#rm)"><g class="rl" fill="{INK_DEEP}" stroke="{SOFT}" stroke-width="1.25" '
           f'stroke-linejoin="round">{"".join(paths)}</g></g>'
           f'<circle class="rec" cx="{x + 26}" cy="{y + 25}" r="4" fill="{EMBER}"/>'
           + text(MONO_M, "LISTENING", 11, x + 38, y + 29, SOFT, track=1.6)
           + text(MONO, "SOAP NOTE · DRAFTING", 11, x + w - 22, y + 29, DIM, anchor="end", track=1.6))
    return defs, art, css


def solid(x, y, w, h):
    """Plato's dodecahedron as a turning ASCII wireframe."""
    shape = a3.dodecahedron()
    base = a3._rotation((1, 0.3, 0), 0.5)
    cols, rows = int(w / CW), int(h / CH)
    n = 40
    frames = []
    for i in range(n):
        rot = a3.spin(i, n, base=base)
        grid = a3.wire_frame(shape, rot, cols, rows, CW, CH, w / 2, h / 2 + 6, 122)
        frames.append(ascii_runs(grid, x, y + CH * 0.78, CW, CH, gap=14))
    clip, svg, css = strip(frames, x, y, cols * CW, rows * CH, rows * CH, 8, "sd")
    labels = (f'<circle cx="{x + 26}" cy="{y + 25}" r="4" fill="{SAFFRON}"/>'
              + text(MONO_M, "ASKING", 11, x + 38, y + 29, SOFT, track=1.6)
              + text(MONO, "WHY DOES THIS LOOP NEVER END?", 11, x + w - 22, y + 29, DIM, anchor="end", track=1.6))
    return clip, f'<g class="a">{svg}</g>' + labels, css + ascii_css(FS, {"f": SOFT, "b": FAINT, "k": SAFFRON})


def project_card(p):
    W, H = 600, 520
    pad = 14
    ix, iy, iw, ih = pad, pad, W - 2 * pad, 300
    kind = p["art"][0]
    defs, art, css = "", "", ""
    if kind == "photo":
        uri = photo_data_uri(p["art"][1], p["slug"], p["art"][2], iw, ih)
        art = (f'<image class="kb" x="{ix}" y="{iy}" width="{iw}" height="{ih}" preserveAspectRatio="xMidYMid slice" href="{uri}"/>'
               f'<rect x="{ix}" y="{iy + ih - 90}" width="{iw}" height="90" fill="url(#shade)"/>')
        css = (f".kb{{transform-origin:{ix + iw / 2}px {iy + ih / 2}px;animation:kb 28s ease-in-out infinite alternate}}"
               "@keyframes kb{to{transform:scale(1.07) translate(-8px,-4px)}}")
        defs = (f'<linearGradient id="shade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{INK_DEEP}" stop-opacity="0"/>'
                f'<stop offset="1" stop-color="{INK_DEEP}" stop-opacity=".45"/></linearGradient>')
    elif kind == "ridgeline":
        defs, art, css = ridgeline(ix, iy, iw, ih)
    else:
        defs, art, css = solid(ix, iy, iw, ih)

    desc_lines = wrap(SANS, p["desc"], 16.5, W - 2 * 30)
    ty = iy + ih + 70
    title = text(SERIF, p["name"], 46, 28, ty, TEXT, track=-0.6)
    kind_label = text(MONO_M, p["kind"], 11.5, W - 30, ty - 6, SAFFRON, anchor="end", track=1.8)
    caption = text(MONO, p["caption"], 10.5, 30, iy + ih + 26, DIM, track=1.4)
    desc = "".join(text(SANS, line, 16.5, 30, ty + 34 + i * 24, MUTED) for i, line in enumerate(desc_lines))
    stack = text(MONO, "  /  ".join(s.upper() for s in p["stack"]), 11, 30, H - 26, DIM, track=1.2)
    ax, ay = W - 38, H - 30
    arrow = (f'<path d="M{ax - 5} {ay + 5}L{ax + 5} {ay - 5}M{ax - 3} {ay - 5}H{ax + 5}V{ay + 3}" fill="none" '
             f'stroke="{SOFT}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>')

    pdefs, open_, close = panel(W, H, 22)
    body = (
        "<defs>" + pdefs + defs
        + f'<clipPath id="img"><rect x="{ix}" y="{iy}" width="{iw}" height="{ih}" rx="12"/></clipPath></defs>'
        + open_
        + f'<rect x="{ix}" y="{iy}" width="{iw}" height="{ih}" rx="12" fill="{INK_DEEP}"/>'
        + f'<g clip-path="url(#img)">{art}</g>'
        + f'<rect x="{ix + .5}" y="{iy + .5}" width="{iw - 1}" height="{ih - 1}" rx="11.5" fill="none" stroke="#fff" stroke-opacity=".06"/>'
        + caption + title + kind_label + desc + stack + arrow
        + close
    )
    write(f"projects/{p['slug']}.svg", document(W, H, f"{p['name']}. {p['desc']}", body, css + REDUCED_MOTION))


# ── toolkit ─────────────────────────────────────────────────────────────────
def toolkit():
    W = 1200
    pad, label_w, line_h, gap_y = 44, 250, 34, 30
    size, sep = 21, 27
    max_x = W - pad
    blocks, y = [], pad + 4
    for i, (label, items) in enumerate(TOOLKIT):
        lines, line, x = [], [], pad + label_w
        for item in items:
            w = SANS.width(item, size, -0.2)
            if line and x + w > max_x:
                lines.append(line)
                line, x = [], pad + label_w
            line.append((item, x))
            x += w + sep
        lines.append(line)
        if i:
            blocks.append(f'<rect x="{pad}" y="{y - gap_y / 2 - 6}" width="{W - 2 * pad}" height="1" fill="{LINE}"/>')
        blocks.append(text(MONO, label.upper(), 12, pad, y + 16, DIM, track=1.6))
        for k, line in enumerate(lines):
            ly = y + 20 + k * line_h
            for j, (item, x) in enumerate(line):
                blocks.append(text(SANS, item, size, x, ly, TEXT, track=-0.2))
                if j < len(line) - 1 or k < len(lines) - 1:
                    sx = x + SANS.width(item, size, -0.2) + sep / 2 - 1.5
                    if j < len(line) - 1:
                        blocks.append(f'<rect x="{num(sx)}" y="{ly - 8}" width="3" height="3" fill="{FAINT}"/>')
        y += line_h * len(lines) + gap_y
    H = y - gap_y + pad - 6
    defs, open_, close = panel(W, H, 22)
    names = "; ".join(f"{label}: {', '.join(items)}" for label, items in TOOLKIT)
    write("toolkit.svg", document(W, H, f"Toolkit. {names}", "<defs>" + defs + "</defs>" + open_ + "".join(blocks) + close))


# ── footer ──────────────────────────────────────────────────────────────────
def footer():
    W, H = 1200, 260
    cx, cy, R = 600, 452, 250
    cols, rows = int(W / CW) + 1, int(H / CH) + 1
    variants = []
    for k, drift in enumerate((0.0, 0.7, 1.4)):
        grid = a3.corona(cols, rows, CW, CH, cx, cy, R, seed=9, sun=(0.0, -1.0), drift=drift, sparkle=k, spread=0.5)
        variants.append(ascii_runs(grid, 0, CH * 0.78, CW, CH))
    glow, glow_css = cycle(variants, 2.4, "cr", order=[0, 1, 2, 1])
    defs, open_, close = panel(W, H, 26)
    body = (
        "<defs>" + defs + "</defs>" + open_
        + f'<g class="a">{ascii_stars(41, W, 150, 36, avoid=[(300, 30, 900, 140)], twinkle=4)}{glow}</g>'
        + f'<circle cx="{cx}" cy="{cy}" r="{R * 0.995}" fill="{INK_DEEP}"/>'
        + text(SERIF, "Thanks for stopping by.", 50, 600, 98, TEXT, anchor="middle", track=-0.5)
        + text(MONO, "LET'S BUILD SOMETHING WORTH SHOWING OFF", 12, 600, 132, MUTED, anchor="middle", track=2.4)
        + close
    )
    css = (ascii_css(FS, {"w": "#FFF4E2", "h": MARIGOLD, "s": SAFFRON, "e": "#D9703A", "d": "#7A4630", "t0": FAINT, "t1": DIM})
           + ".tw{animation:tw 3.2s ease-in-out infinite alternate}@keyframes tw{from{opacity:.15}to{opacity:1}}"
           + glow_css + REDUCED_MOTION)
    write("footer.svg", document(W, H, "Thanks for stopping by. Let's build something worth showing off.", body, css))


if __name__ == "__main__":
    print("building assets/")
    header()
    for slug, label, icon in KEYS:
        keycap(slug, label, icon)
    section_titles()
    for project in PROJECTS:
        project_card(project)
    toolkit()
    footer()
