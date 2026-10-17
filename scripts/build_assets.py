#!/usr/bin/env python3
"""Builds the SVG artwork used by README.md.

GitHub serves README images in a sandbox that can't load web fonts, so every
piece of text is shaped with HarfBuzz and baked into vector paths. The fonts
(Space Grotesk and JetBrains Mono, both SIL OFL) and the tech icons are
downloaded once into scripts/.cache/.

    pip install fonttools uharfbuzz
    python3 scripts/build_assets.py

Edit the content in PROJECTS, STACK and LANGUAGES below, then rebuild.
"""

import io
import math
import random
import re
import urllib.request
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

HERE = Path(__file__).resolve().parent
CACHE = HERE / ".cache"
ASSETS = HERE.parent / "assets"

# ── palette: deep ink with a saffron corona ─────────────────────────────────
INK = "#0C0E1C"
INK_DEEP = "#090A15"
INK_HIGH = "#11142B"
SURFACE = "#151935"
LINE = "#232847"
TEXT = "#F3F1EC"
SOFT = "#C9CCE0"
MUTED = "#A6ABC8"
DIM = "#6E7396"
SAFFRON = "#FFA552"
MARIGOLD = "#FFC56E"
EMBER = "#FF6B4A"
ROSE = "#F2668B"
VIOLET = "#9B7BFF"
INDIGO = "#5B7CFF"
MINT = "#3DD9B4"

LIGHT_TEXT = "#12142A"
LIGHT_ACCENT = "#D9670F"

FONT_URLS = {
    "grotesk": "https://github.com/google/fonts/raw/main/ofl/spacegrotesk/SpaceGrotesk%5Bwght%5D.ttf",
    "mono": "https://github.com/google/fonts/raw/main/ofl/jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf",
}

REDUCED_MOTION = "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"


# ── content ─────────────────────────────────────────────────────────────────
PROJECTS = [
    {
        "slug": "stratos",
        "name": "Stratos",
        "kicker": "FLIGHT GAME · WEBGL",
        "desc": "An open-world fighter jet game for the browser: physically based "
                "skies, volumetric storms and nine jets, from the wavetops to the "
                "edge of space.",
        "tags": ["Three.js", "WebGL 2", "Rapier", "TypeScript"],
        "accent": "#6C8CFF",
        "icon": "jet",
    },
    {
        "slug": "yudhveer",
        "name": "Yudhveer",
        "kicker": "ACTION GAME · WEBGL",
        "desc": "An Indian mythological action game. Cel-shaded sword-and-shield "
                "combat across five worlds, with bosses that block and parry back.",
        "tags": ["Three.js", "Rapier", "TypeScript", "Vite"],
        "accent": "#FF8A3D",
        "icon": "sword",
    },
    {
        "slug": "echoscribe",
        "name": "EchoScribe",
        "kicker": "CLINICAL AI",
        "desc": "An ambient clinical scribe that turns doctor–patient conversations "
                "into structured, FHIR-ready SOAP notes in real time.",
        "tags": ["React", "FastAPI", "BioNLP", "FHIR R4"],
        "accent": MINT,
        "icon": "wave",
    },
    {
        "slug": "socra",
        "name": "Socra",
        "kicker": "AI FOR EDUCATION",
        "desc": "A Socratic AI learning platform for UB's intro CS courses, with "
                "guided hints, sandboxed code runs, adaptive practice and faculty "
                "analytics.",
        "tags": ["TypeScript", "Postgres", "Redis", "Docker"],
        "accent": "#B18CFF",
        "icon": "chat",
    },
]

# skillicons.dev ids, or a key of CUSTOM_ICONS
STACK = [
    ("Languages", ["ts", "js", "py", "java", "c", "html", "css"]),
    ("Frontend", ["react", "nextjs", "vue", "tailwind", "threejs", "framer"]),
    ("Backend & cloud", ["nodejs", "firebase", "mongodb", "mysql", "aws", "gcp", "azure", "kubernetes", "vercel"]),
    ("ML & data", ["pytorch", "tensorflow", "sklearn", "opencv", "pandas"]),
    ("Design & games", ["figma", "pr", "godot"]),
    ("AI tooling", ["claude", "lovable", "antigravity", "openclaw"]),
]

CUSTOM_ICONS = {
    "framer": "https://www.vectorlogo.zone/logos/framer/framer-icon.svg",
    "pandas": "https://raw.githubusercontent.com/devicons/devicon/2ae2a900d2f041da66e950e4d48052658d850630/icons/pandas/pandas-original.svg",
    "claude": "https://devicons.io/devicons/icons/claude-code.svg",
    "lovable": "https://devicons.io/devicons/icons/lovable-icon.svg",
    "antigravity": "https://raw.githubusercontent.com/lobehub/lobe-icons/refs/heads/master/packages/static-svg/icons/antigravity-color.svg",
    "openclaw": "https://devicons.io/devicons/icons/openclaw.svg",
}
# dark parts of a logo that would vanish on the dark tile
ICON_RECOLOR = {"pandas": {"#130754": "#E6E4F2"}}

# Share of code across public, non-fork repos, weighted like github-readme-stats
# (sqrt(bytes) × sqrt(repo count)), top six renormalised. Snapshot: Oct 2026.
LANGUAGES = [
    ("TypeScript", 43),
    ("JavaScript", 21),
    ("CSS", 12),
    ("HTML", 11),
    ("Python", 7),
    ("GDScript", 6),
]
LANGUAGE_COLORS = [SAFFRON, EMBER, ROSE, VIOLET, INDIGO, MINT]

SECTIONS = [
    ("about", "01", "About"),
    ("work", "02", "Featured work"),
    ("stack", "03", "Tech stack"),
    ("stats", "04", "GitHub stats"),
    ("contributions", "05", "Contribution graph"),
]


# ── fetching ────────────────────────────────────────────────────────────────
def fetch(url, name):
    path = CACHE / name
    if not path.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 build_assets"})
        with urllib.request.urlopen(request, timeout=30) as response:
            path.write_bytes(response.read())
    return path


# ── type ────────────────────────────────────────────────────────────────────
def num(n):
    s = f"{n:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


class Font:
    def __init__(self, family, weight):
        static = instantiateVariableFont(TTFont(fetch(FONT_URLS[family], f"{family}.ttf")), {"wght": weight})
        buffer = io.BytesIO()
        static.save(buffer)
        data = buffer.getvalue()
        self.tt = TTFont(io.BytesIO(data))
        self.glyphs = self.tt.getGlyphSet()
        self.order = self.tt.getGlyphOrder()
        self.upem = self.tt["head"].unitsPerEm
        self.hb = hb.Font(hb.Face(data))

    def _shape(self, s):
        buffer = hb.Buffer()
        buffer.add_str(s)
        buffer.guess_segment_properties()
        hb.shape(self.hb, buffer, {"kern": True, "liga": True})
        return list(zip(buffer.glyph_infos, buffer.glyph_positions))

    def width(self, s, size, track=0.0):
        glyphs = self._shape(s)
        scale = size / self.upem
        return sum(pos.x_advance * scale + track for _, pos in glyphs) - (track if glyphs else 0)

    def path(self, s, size, x, y, anchor="start", track=0.0):
        if anchor != "start":
            w = self.width(s, size, track)
            x -= w if anchor == "end" else w / 2
        scale = size / self.upem
        pen = SVGPathPen(self.glyphs, ntos=num)
        for info, pos in self._shape(s):
            gx, gy = x + pos.x_offset * scale, y - pos.y_offset * scale
            self.glyphs[self.order[info.codepoint]].draw(TransformPen(pen, (scale, 0, 0, -scale, gx, gy)))
            x += pos.x_advance * scale + track
        return pen.getCommands()


G7 = Font("grotesk", 700)
G6 = Font("grotesk", 600)
G5 = Font("grotesk", 500)
G4 = Font("grotesk", 400)
M5 = Font("mono", 500)
M4 = Font("mono", 400)


def text(font, s, size, x, y, fill, anchor="start", track=0.0, attrs=""):
    return f'<path fill="{fill}"{attrs} d="{font.path(s, size, x, y, anchor, track)}"/>'


def wrap(font, s, size, max_width):
    lines, line = [], ""
    for word in s.split():
        candidate = f"{line} {word}".strip()
        if line and font.width(candidate, size) > max_width:
            lines.append(line)
            line = word
        else:
            line = candidate
    return lines + [line]


def pill(font, label, x, y, height, size, fg, bg, stroke, pad=14):
    w = font.width(label, size) + 2 * pad
    shape = f'<rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{height}" rx="{height / 2}" fill="{bg}" stroke="{stroke}"/>'
    return w, shape + text(font, label, size, x + pad, y + height / 2 + size * 0.36, fg)


def document(w, h, title, body, css=""):
    title = title.replace("&", "&amp;")
    style = f"<style>{css}</style>" if css else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{title}">'
        f"<title>{title}</title>{style}{body}</svg>\n"
    )


def write(name, svg):
    path = ASSETS / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")
    print(f"  {path.relative_to(HERE.parent)}  {len(svg.encode()) / 1024:.1f} KB")


def stars(rnd, w, h, count, avoid=None, twinkle=0.3):
    out = []
    for _ in range(count):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        if avoid and math.dist((x, y), avoid[:2]) < avoid[2]:
            continue
        r = rnd.choice([0.6, 0.8, 0.8, 1.0, 1.2, 1.5])
        color = "#FFE3C2" if rnd.random() < 0.25 else "#FFFFFF"
        if rnd.random() < twinkle:
            timing = f"animation-duration:{rnd.uniform(2.5, 6):.1f}s;animation-delay:-{rnd.uniform(0, 6):.1f}s"
            out.append(f'<circle class="tw" cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{color}" style="{timing}"/>')
        else:
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{color}" opacity="{rnd.uniform(0.2, 0.75):.2f}"/>')
    return "".join(out)


def card_frame(w, h, rx, gid="bg"):
    return (
        f'<linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{INK_DEEP}"/><stop offset="1" stop-color="{INK_HIGH}"/></linearGradient>'
        f'<clipPath id="card"><rect width="{w}" height="{h}" rx="{rx}"/></clipPath>'
    )


# ── header ──────────────────────────────────────────────────────────────────
def header():
    W, H = 1200, 440
    cx, cy, R = 912, 214, 112
    x0 = 84
    rnd = random.Random(11)
    a = math.radians(-38)
    dx, dy = cx + R * math.cos(a), cy + R * math.sin(a)

    streamers = []
    for i in range(16):
        angle = i * 360 / 16 + rnd.uniform(-9, 9)
        length = rnd.uniform(48, 112)
        dist = R + length * 0.5
        ex = cx + dist * math.cos(math.radians(angle))
        ey = cy + dist * math.sin(math.radians(angle))
        streamers.append(
            f'<ellipse cx="{ex:.1f}" cy="{ey:.1f}" rx="{length:.1f}" ry="{rnd.uniform(4, 10):.1f}" '
            f'transform="rotate({angle:.1f} {ex:.1f} {ey:.1f})" fill="{rnd.choice([SAFFRON, MARIGOLD, "#FFD9A6"])}" '
            f'opacity="{rnd.uniform(0.22, 0.5):.2f}"/>'
        )

    defs = (
        "<defs>"
        + card_frame(W, H, 28)
        + f'<radialGradient id="haze" cx="{cx}" cy="{cy}" r="360" gradientUnits="userSpaceOnUse">'
        f'<stop offset=".28" stop-color="#FF8A3D" stop-opacity=".30"/>'
        f'<stop offset=".6" stop-color="{ROSE}" stop-opacity=".07"/>'
        f'<stop offset="1" stop-color="{INDIGO}" stop-opacity="0"/></radialGradient>'
        f'<radialGradient id="moon" cx="{cx - 46}" cy="{cy - 52}" r="{R * 1.5}" gradientUnits="userSpaceOnUse">'
        f'<stop offset="0" stop-color="#1B1D31"/><stop offset="1" stop-color="#040509"/></radialGradient>'
        f'<linearGradient id="name" x1="{x0}" x2="{x0 + 640}" gradientUnits="userSpaceOnUse">'
        f'<stop offset="0" stop-color="#FFFFFF"/><stop offset=".55" stop-color="#FFF1E2"/><stop offset="1" stop-color="#FFC897"/></linearGradient>'
        f'<linearGradient id="flareH" x1="-110" x2="110" gradientUnits="userSpaceOnUse">'
        f'<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        f'<linearGradient id="flareV" y1="-56" y2="56" x1="0" x2="0" gradientUnits="userSpaceOnUse">'
        f'<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        f'<linearGradient id="streak" x1="0" y1="0" x2="-96" y2="-38" gradientUnits="userSpaceOnUse">'
        f'<stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        '<filter id="b60" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="60"/></filter>'
        '<filter id="b22" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="22"/></filter>'
        '<filter id="b8" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="8"/></filter>'
        '<filter id="b3" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.5"/></filter>'
        "</defs>"
    )

    corona = (
        f'<circle cx="{cx}" cy="{cy}" r="360" fill="url(#haze)"/>'
        f'<g class="pulse">'
        f'<circle cx="{cx}" cy="{cy}" r="{R + 16}" fill="none" stroke="#FF9F4A" stroke-width="36" filter="url(#b22)"/>'
        f'<g class="spin" filter="url(#b8)">{"".join(streamers)}</g>'
        f"</g>"
        f'<circle cx="{cx}" cy="{cy}" r="{R + 2}" fill="none" stroke="#FFE2B8" stroke-width="5" filter="url(#b3)"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="url(#moon)"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="#FFEBD2" stroke-opacity=".75" stroke-width="1.2"/>'
        f'<g transform="translate({dx:.1f} {dy:.1f})"><g class="flare">'
        f'<circle r="26" fill="#FFD9A6" opacity=".9" filter="url(#b8)"/>'
        f'<line x1="-110" x2="110" stroke="url(#flareH)" stroke-width="1.6"/>'
        f'<line y1="-56" y2="56" stroke="url(#flareV)" stroke-width="1.4"/>'
        f'<circle r="5" fill="#FFFFFF"/></g></g>'
    )

    nebula = (
        f'<ellipse cx="170" cy="460" rx="420" ry="150" fill="{INDIGO}" opacity=".22" filter="url(#b60)"/>'
        f'<ellipse cx="560" cy="-30" rx="320" ry="90" fill="{VIOLET}" opacity=".14" filter="url(#b60)"/>'
    )

    shooting = (
        '<g transform="translate(560 44)"><g class="shoot">'
        '<line x1="0" y1="0" x2="-96" y2="-38" stroke="url(#streak)" stroke-width="1.6" stroke-linecap="round"/>'
        '<circle r="1.7" fill="#fff"/></g></g>'
    )

    kicker = (
        f'<line x1="{x0}" y1="{144}" x2="{x0 + 30}" y2="{144}" stroke="{SAFFRON}" stroke-width="2"/>'
        + text(M5, "HELLO, I'M", 17, x0 + 44, 150, SAFFRON, track=4)
    )

    name = "Tejas Govind"
    name_w = G7.width(name, 96, -2.5)
    title = (
        text(G7, name, 96, x0, 236, "url(#name)", track=-2.5)
        + f'<rect class="cursor" x="{num(x0 + name_w + 14)}" y="166" width="7" height="76" rx="2" fill="{SAFFRON}"/>'
    )

    tagline, x = [], x0
    for i, word in enumerate(["Developer", "Builder", "Lifelong learner"]):
        tagline.append(text(G5, word, 28, x, 292, SOFT))
        x += G5.width(word, 28)
        if i < 2:
            tagline.append(f'<circle cx="{num(x + 17)}" cy="283" r="3.2" fill="{SAFFRON}"/>')
            x += 34

    pills, x = [], x0
    for label in ["CS @ University at Buffalo", "Full-stack", "Game dev", "AI / ML"]:
        w, shape = pill(M5, label, x, 326, 38, 15, "#D9DBEA", "#151935", "#2A3060")
        pills.append(shape)
        x += w + 10

    coords = text(M4, "BUFFALO, NY · 42.89° N · 78.88° W", 13, W - 44, H - 36, DIM, anchor="end", track=2)

    css = (
        ".tw{animation:tw 4s ease-in-out infinite alternate}"
        "@keyframes tw{from{opacity:.12}to{opacity:.9}}"
        ".pulse{animation:pulse 7s ease-in-out infinite alternate}"
        "@keyframes pulse{from{opacity:.72}to{opacity:1}}"
        f".spin{{transform-origin:{cx}px {cy}px;animation:spin 240s linear infinite}}"
        "@keyframes spin{to{transform:rotate(360deg)}}"
        ".flare{animation:flare 3.4s ease-in-out infinite alternate}"
        "@keyframes flare{from{opacity:.7;transform:scale(.82)}to{opacity:1;transform:scale(1.08)}}"
        ".cursor{animation:blink 1.1s steps(1) infinite}"
        "@keyframes blink{50%{opacity:0}}"
        ".shoot{opacity:0;animation:shoot 11s ease-in 3s infinite}"
        "@keyframes shoot{0%{opacity:0;transform:none}2%{opacity:1}9%{opacity:0;transform:translate(220px,88px)}100%{opacity:0;transform:translate(220px,88px)}}"
        + REDUCED_MOTION
    )

    body = (
        defs
        + '<g clip-path="url(#card)">'
        + f'<rect width="{W}" height="{H}" fill="url(#bg)"/>'
        + nebula
        + stars(rnd, W, H, 110, avoid=(cx, cy, R + 8))
        + shooting
        + corona
        + kicker
        + title
        + "".join(tagline)
        + "".join(pills)
        + coords
        + "</g>"
        + f'<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="27.5" fill="none" stroke="{LINE}" stroke-width="1.5"/>'
    )
    write("header.svg", document(W, H, "Tejas Govind — Developer · Builder · Lifelong learner", body, css))


# ── footer ──────────────────────────────────────────────────────────────────
def footer():
    W, H = 1200, 170
    rnd = random.Random(5)
    limb_r = 1500
    limb_cy = 132 + limb_r
    defs = (
        "<defs>"
        + card_frame(W, H, 28)
        + f'<radialGradient id="sun" cx="600" cy="132" r="260" gradientUnits="userSpaceOnUse">'
        f'<stop offset="0" stop-color="#FFB86B" stop-opacity=".55"/><stop offset=".4" stop-color="{EMBER}" stop-opacity=".12"/>'
        f'<stop offset="1" stop-color="{EMBER}" stop-opacity="0"/></radialGradient>'
        f'<linearGradient id="rim" x1="0" x2="{W}" gradientUnits="userSpaceOnUse">'
        f'<stop offset="0" stop-color="{SAFFRON}" stop-opacity="0"/><stop offset=".5" stop-color="#FFE2B8"/>'
        f'<stop offset="1" stop-color="{SAFFRON}" stop-opacity="0"/></linearGradient>'
        '<filter id="b10" x="-20%" y="-200%" width="140%" height="500%"><feGaussianBlur stdDeviation="10"/></filter>'
        "</defs>"
    )
    body = (
        defs
        + '<g clip-path="url(#card)">'
        + f'<rect width="{W}" height="{H}" fill="url(#bg)"/>'
        + stars(rnd, W, 120, 60)
        + f'<ellipse class="pulse" cx="600" cy="132" rx="420" ry="150" fill="url(#sun)"/>'
        + f'<circle cx="600" cy="{limb_cy}" r="{limb_r}" fill="none" stroke="{SAFFRON}" stroke-width="10" opacity=".55" filter="url(#b10)"/>'
        + f'<circle cx="600" cy="{limb_cy}" r="{limb_r}" fill="#05060B" stroke="url(#rim)" stroke-width="1.6"/>'
        + text(G6, "Thanks for stopping by.", 32, 600, 74, TEXT, anchor="middle", track=-0.5)
        + text(M4, "LET'S BUILD SOMETHING WORTH SHOWING OFF", 13, 600, 104, MUTED, anchor="middle", track=3)
        + "</g>"
        + f'<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="27.5" fill="none" stroke="{LINE}" stroke-width="1.5"/>'
    )
    css = (
        ".tw{animation:tw 4s ease-in-out infinite alternate}@keyframes tw{from{opacity:.12}to{opacity:.9}}"
        ".pulse{animation:pulse 6s ease-in-out infinite alternate}@keyframes pulse{from{opacity:.65}to{opacity:1}}"
        + REDUCED_MOTION
    )
    write("footer.svg", document(W, H, "Thanks for stopping by", body, css))


# ── section titles (light + dark) ───────────────────────────────────────────
def section_titles():
    W, H = 1200, 64
    for slug, index, label in SECTIONS:
        for theme, fg, accent in (("dark", TEXT, SAFFRON), ("light", LIGHT_TEXT, LIGHT_ACCENT)):
            ix = M5.width(index, 17, 1) + 20
            lx = ix + G6.width(label, 34, -0.5) + 28
            body = (
                f'<defs><linearGradient id="fade" x1="{num(lx)}" x2="{W}" gradientUnits="userSpaceOnUse">'
                f'<stop offset="0" stop-color="{accent}" stop-opacity=".7"/><stop offset="1" stop-color="{accent}" stop-opacity="0"/>'
                f"</linearGradient></defs>"
                + text(M5, index, 17, 0, 44, accent, track=1)
                + text(G6, label, 34, ix, 44, fg, track=-0.5)
                + f'<rect x="{num(lx)}" y="31" width="{num(W - lx)}" height="1.5" fill="url(#fade)"/>'
            )
            write(f"titles/{slug}-{theme}.svg", document(W, H, label, body))


# ── project cards ───────────────────────────────────────────────────────────
ICONS = {
    "jet": '<path fill="{c}" d="M12 1.5l1.6 7.2 7.9 4.4v2.1l-7.9-2.1-.5 5.4 3.1 2.1v1.4L12 21l-4.2 1v-1.4l3.1-2.1-.5-5.4-7.9 2.1v-2.1l7.9-4.4z"/>',
    "sword": '<g fill="none" stroke="{c}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
             '<path d="M12 1.8l2 3v10h-4v-10z"/><path d="M6.5 14.8h11M12 14.8v4.6"/><circle cx="12" cy="21" r="1.4"/></g>',
    "wave": '<g stroke="{c}" stroke-width="2" stroke-linecap="round">'
            '<path d="M3.5 10v4M7 7v10M10.5 3.5v17M14 8v8M17.5 5.5v13M21 10.5v3"/></g>',
    "chat": '<path fill="none" stroke="{c}" stroke-width="1.8" stroke-linejoin="round" '
            'd="M5 4h14a2.5 2.5 0 0 1 2.5 2.5v8A2.5 2.5 0 0 1 19 17h-8l-4.5 3.8V17H5a2.5 2.5 0 0 1-2.5-2.5v-8A2.5 2.5 0 0 1 5 4z"/>'
            '<g fill="{c}"><circle cx="8" cy="10.5" r="1.3"/><circle cx="12" cy="10.5" r="1.3"/><circle cx="16" cy="10.5" r="1.3"/></g>',
}


def project_card(p):
    W, H = 600, 310
    accent = p["accent"]
    pad = 34
    desc_lines = wrap(G4, p["desc"], 18, W - 2 * pad)
    body_top = 172

    tile = (
        f'<rect x="{pad}" y="32" width="54" height="54" rx="15" fill="{accent}" fill-opacity=".12" stroke="{accent}" stroke-opacity=".35"/>'
        f'<g transform="translate({pad + 9} 41) scale(1.5)">{ICONS[p["icon"]].format(c=accent)}</g>'
    )
    kicker = text(M5, p["kicker"], 13, pad + 72, 64, accent, track=2.2)
    title = text(G7, p["name"], 36, pad, 138, TEXT, track=-0.8)
    desc = "".join(text(G4, line, 18, pad, body_top + i * 25, MUTED) for i, line in enumerate(desc_lines))

    tags, x = [], pad
    for tag in p["tags"]:
        w, shape = pill(M5, tag, x, H - 64, 30, 13, SOFT, SURFACE, "#262C55", pad=12)
        tags.append(shape)
        x += w + 8

    ax, ay = W - pad - 17, H - 49
    arrow = (
        f'<circle cx="{ax}" cy="{ay}" r="17" fill="{accent}" fill-opacity=".12" stroke="{accent}" stroke-opacity=".5"/>'
        f'<path d="M{ax - 5} {ay + 5}L{ax + 5} {ay - 5}M{ax - 3} {ay - 5}H{ax + 5}V{ay + 3}" fill="none" stroke="{accent}" '
        f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
    )

    body = (
        "<defs>"
        + card_frame(W, H, 22)
        + f'<radialGradient id="glow" cx="{W - 40}" cy="0" r="340" gradientUnits="userSpaceOnUse">'
        f'<stop offset="0" stop-color="{accent}" stop-opacity=".26"/><stop offset="1" stop-color="{accent}" stop-opacity="0"/></radialGradient>'
        "</defs>"
        + '<g clip-path="url(#card)">'
        + f'<rect width="{W}" height="{H}" fill="url(#bg)"/>'
        + f'<rect width="{W}" height="{H}" fill="url(#glow)"/>'
        + stars(random.Random(p["slug"]), W, 120, 18, twinkle=0)
        + tile + kicker + title + desc + "".join(tags) + arrow
        + "</g>"
        + f'<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="21.5" fill="none" stroke="{LINE}" stroke-width="1.5"/>'
    )
    write(f"projects/{p['slug']}.svg", document(W, H, f"{p['name']} — {p['desc']}", body))


# ── tech stack ──────────────────────────────────────────────────────────────
def scope_ids(svg, prefix):
    for i in sorted(set(re.findall(r'\bid="([^"]+)"', svg)), key=len, reverse=True):
        svg = svg.replace(f'id="{i}"', f'id="{prefix}{i}"')
        svg = svg.replace(f"url(#{i})", f"url(#{prefix}{i})")
        svg = svg.replace(f'href="#{i}"', f'href="#{prefix}{i}"')
    return svg


def inline_classes(svg):
    style = re.search(r"<style[^>]*>(.*?)</style>", svg, re.S)
    if style:
        for name, decls in re.findall(r"\.([\w-]+)\s*\{([^}]*)\}", style.group(1)):
            svg = svg.replace(f'class="{name}"', f'style="{decls.strip()}"')
        svg = svg.replace(style.group(0), "")
    return svg


def tile(icon, x, y, size):
    if icon in CUSTOM_ICONS:
        raw = fetch(CUSTOM_ICONS[icon], f"logo-{icon}.svg").read_text(encoding="utf-8")
        raw = re.sub(r"<\?xml.*?\?>|<!--.*?-->|<title>.*?</title>", "", raw, flags=re.S)
        raw = inline_classes(raw)
        for old, new in ICON_RECOLOR.get(icon, {}).items():
            raw = raw.replace(old, new)
        attrs, inner = re.search(r"<svg\b([^>]*)>(.*)</svg>", raw, re.S).groups()
        view_box = re.search(r'viewBox="([^"]+)"', attrs).group(1)
        fill = re.search(r'\bfill="([^"]+)"', attrs)
        fill = f' fill="{fill.group(1)}"' if fill else ""
        content = (
            f'<rect width="256" height="256" rx="60" fill="#242938"/>'
            f'<svg x="56" y="56" width="144" height="144" viewBox="{view_box}"{fill}>{inner}</svg>'
        )
    else:
        raw = fetch(f"https://skillicons.dev/icons?i={icon}", f"skill-{icon}.svg").read_text(encoding="utf-8")
        content = re.search(r"<svg\b[^>]*>(.*)</svg>", raw, re.S).group(1)
    content = scope_ids(content, f"{icon}-")
    return f'<svg x="{x}" y="{y}" width="{size}" height="{size}" viewBox="0 0 256 256">{content}</svg>'


def stack():
    W = 1000
    pad, label_w, size, gap, pitch = 44, 236, 58, 14, 84
    H = pad * 2 + pitch * (len(STACK) - 1) + size
    rows = []
    for i, (label, icons) in enumerate(STACK):
        y = pad + i * pitch
        if i:
            rows.append(f'<rect x="{pad}" y="{y - (pitch - size) / 2 - 0.5}" width="{W - 2 * pad}" height="1" fill="{LINE}" opacity=".7"/>')
        rows.append(text(M5, f"0{i + 1}", 12, pad, y + size / 2 + 5, SAFFRON, track=1))
        rows.append(text(G5, label, 20, pad + 34, y + size / 2 + 7, TEXT, track=-0.2))
        for j, icon in enumerate(icons):
            rows.append(tile(icon, pad + label_w + j * (size + gap), y, size))
    body = (
        "<defs>" + card_frame(W, H, 22) + "</defs>"
        + '<g clip-path="url(#card)">'
        + f'<rect width="{W}" height="{H}" fill="url(#bg)"/>'
        + "".join(rows)
        + "</g>"
        + f'<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="21.5" fill="none" stroke="{LINE}" stroke-width="1.5"/>'
    )
    names = ", ".join(i for _, icons in STACK for i in icons)
    write("stack.svg", document(W, H, f"Tech stack: {names}", body))


# ── languages (sized to sit beside the streak card) ────────────────────────
def languages():
    W, H = 495, 195
    pad = 26
    total = sum(v for _, v in LANGUAGES)
    bar_w, x = W - 2 * pad, pad
    segments = []
    for (name, value), color in zip(LANGUAGES, LANGUAGE_COLORS):
        w = bar_w * value / total
        segments.append(f'<rect x="{num(x)}" y="62" width="{num(max(w - 3, 1))}" height="10" fill="{color}"/>')
        x += w
    legend = []
    col_w = (W - 2 * pad) / 2
    for i, ((name, value), color) in enumerate(zip(LANGUAGES, LANGUAGE_COLORS)):
        lx = pad + (i % 2) * (col_w + 6)
        ly = 112 + (i // 2) * 30
        legend.append(f'<circle cx="{num(lx + 5)}" cy="{ly - 5}" r="5" fill="{color}"/>')
        legend.append(text(G5, name, 16, lx + 20, ly, TEXT))
        legend.append(text(M4, f"{value}%", 14, lx + col_w - 18, ly, MUTED, anchor="end"))
    body = (
        f'<defs><clipPath id="bar"><rect x="{pad}" y="62" width="{bar_w}" height="10" rx="5"/></clipPath></defs>'
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16" fill="{INK}" stroke="{LINE}"/>'
        + text(G6, "Top languages", 19, pad, 40, TEXT, track=-0.2)
        + text(M4, "BY CODE SHARE", 11, W - pad, 39, DIM, anchor="end", track=2)
        + f'<g clip-path="url(#bar)">{"".join(segments)}</g>'
        + "".join(legend)
    )
    write("languages.svg", document(W, H, "Top languages: " + ", ".join(f"{n} {v}%" for n, v in LANGUAGES), body))


if __name__ == "__main__":
    print("building assets/")
    header()
    footer()
    section_titles()
    for project in PROJECTS:
        project_card(project)
    stack()
    languages()
