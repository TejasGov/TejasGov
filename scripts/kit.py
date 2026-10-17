"""Shared drawing kit for the profile artwork.

GitHub serves README images in a sandbox that can't load web fonts, so display
type is shaped with HarfBuzz and baked into vector paths. ASCII art is the one
exception: it is set as real <text> in the reader's system monospace font, with
textLength pinning every run to the character grid so it lines up in any font.
"""

import io
import random
import urllib.request
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

HERE = Path(__file__).resolve().parent
CACHE = HERE / ".cache"
ASSETS = HERE.parent / "assets"

# ── palette: deep ink, one saffron accent ───────────────────────────────────
INK = "#0B0D18"
INK_DEEP = "#08090F"
INK_HIGH = "#10132A"
SURFACE = "#151935"
LINE = "#222744"
TEXT = "#F3F1EC"
SOFT = "#C9CCE0"
MUTED = "#9EA3C0"
DIM = "#646987"
FAINT = "#3A3F5E"
SAFFRON = "#FFA552"
MARIGOLD = "#FFC56E"
EMBER = "#FF6B4A"

LIGHT_TEXT = "#12142A"
LIGHT_MUTED = "#5A5F7A"
LIGHT_ACCENT = "#C85F0C"

FONT_URLS = {
    "serif": "https://github.com/google/fonts/raw/main/ofl/instrumentserif/InstrumentSerif-Regular.ttf",
    "sans": "https://github.com/google/fonts/raw/main/ofl/geist/Geist%5Bwght%5D.ttf",
    "mono": "https://github.com/google/fonts/raw/main/ofl/geistmono/GeistMono%5Bwght%5D.ttf",
}

ASCII_FONT = 'ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono","DejaVu Sans Mono",monospace'
REDUCED_MOTION = "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"


def fetch(url, name):
    path = CACHE / name
    if not path.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 build_assets"})
        with urllib.request.urlopen(request, timeout=30) as response:
            path.write_bytes(response.read())
    return path


def num(n):
    s = f"{n:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def num4(n):
    s = f"{n:.5f}".rstrip("0").rstrip(".")
    return s.replace("0.", ".", 1) if s.startswith(("0.", "-0.")) else s


# ── type ────────────────────────────────────────────────────────────────────
class Font:
    def __init__(self, family, weight=None):
        font = TTFont(fetch(FONT_URLS[family], f"{family}.ttf"))
        if "fvar" in font:
            font = instantiateVariableFont(font, {"wght": weight})
        buffer = io.BytesIO()
        font.save(buffer)
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

    def outline(self, gid):
        pen = SVGPathPen(self.glyphs, ntos=lambda n: str(round(n)))
        self.glyphs[self.order[gid]].draw(pen)
        return pen.getCommands()

    def uses(self, s, size, x, y, anchor="start", track=0.0):
        """Glyph ids and positions in font units, for a group scaled to `size`."""
        if anchor != "start":
            w = self.width(s, size, track)
            x -= w if anchor == "end" else w / 2
        scale = size / self.upem
        pen_x, placed = 0.0, []
        for info, pos in self._shape(s):
            placed.append((info.codepoint, pen_x + pos.x_offset, pos.y_offset))
            pen_x += pos.x_advance + track / scale
        return x, y, scale, placed


class Glyphs:
    """Collects the glyphs a document uses so each outline is written once."""

    def __init__(self):
        self.ids = {}
        self.defs = []

    def ref(self, f, gid):
        """Short id for the glyph's outline, or None for an empty glyph (a space)."""
        key = (id(f), gid)
        if key not in self.ids:
            d = f.outline(gid)
            self.ids[key] = _short(len(self.defs)) if d else None
            if d:
                self.defs.append(f'<path id="{self.ids[key]}" d="{d}"/>')
        return self.ids[key]

    def flush(self):
        out = f"<defs>{''.join(self.defs)}</defs>" if self.defs else ""
        self.ids, self.defs = {}, []
        return out


def _short(i):
    letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    out = ""
    i += 1
    while i:
        i, r = divmod(i - 1, len(letters))
        out = letters[r] + out
    return "g" + out


GLYPHS = Glyphs()


_fonts = {}


def font(family, weight=None):
    key = (family, weight)
    if key not in _fonts:
        _fonts[key] = Font(family, weight)
    return _fonts[key]


def text(f, s, size, x, y, fill, anchor="start", track=0.0, attrs=""):
    x, y, scale, placed = f.uses(s, size, x, y, anchor, track)
    uses = []
    for gid, gx, gy in placed:
        ref = GLYPHS.ref(f, gid)
        if ref:
            uses.append(f'<use href="#{ref}"' + (f' x="{round(gx)}"' if round(gx) else "")
                        + (f' y="{round(gy)}"' if round(gy) else "") + "/>")
    uses = "".join(uses)
    return f'<g fill="{fill}"{attrs} transform="matrix({num4(scale)} 0 0 {num4(-scale)} {num(x)} {num(y)})">{uses}</g>'


def wrap(f, s, size, max_width):
    lines, line = [], ""
    for word in s.split():
        candidate = f"{line} {word}".strip()
        if line and f.width(candidate, size) > max_width:
            lines.append(line)
            line = word
        else:
            line = candidate
    return lines + [line]


# ── documents ───────────────────────────────────────────────────────────────
def document(w, h, title, body, css=""):
    title = title.replace("&", "&amp;").replace('"', "&quot;")
    style = f"<style>{css}</style>" if css else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{title}">'
        f"<title>{title}</title>{style}{GLYPHS.flush()}{body}</svg>\n"
    )


def write(name, svg, root=ASSETS):
    path = Path(root) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")
    print(f"  {name}  {len(svg.encode()) / 1024:.1f} KB")


def panel(w, h, rx=22, gid="bg"):
    """Background gradient + clip for a dark card. Returns (defs, open, close)."""
    defs = (
        f'<linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{INK_DEEP}"/><stop offset="1" stop-color="{INK_HIGH}"/></linearGradient>'
        f'<clipPath id="card"><rect width="{w}" height="{h}" rx="{rx}"/></clipPath>'
    )
    open_ = f'<g clip-path="url(#card)"><rect width="{w}" height="{h}" fill="url(#{gid})"/>'
    close = (
        "</g>"
        f'<rect x=".75" y=".75" width="{num(w - 1.5)}" height="{num(h - 1.5)}" rx="{num(rx - 0.5)}" '
        f'fill="none" stroke="{LINE}" stroke-width="1.5"/>'
    )
    return defs, open_, close


# ── ASCII ───────────────────────────────────────────────────────────────────
def ascii_css(size, cls_colors):
    """CSS for ASCII layers: font, whitespace, and one class per colour."""
    rules = [f".a text{{font:{size}px {ASCII_FONT};white-space:pre}}"]
    rules += [f".a .{c}{{fill:{color}}}" for c, color in cls_colors.items()]
    return "".join(rules)


def ascii_runs(rows, x0, y0, cw, ch, gap=5):
    """rows: list of lists of (char, cls) or None. Emits one <text> per run of a
    class, splitting runs at gaps wider than `gap` cells, with textLength pinned
    to the grid so the art lines up in whatever monospace font the reader has."""
    out = {}
    for r, row in enumerate(rows):
        by_cls = {}
        for c, cell in enumerate(row):
            if cell and cell[0] != " ":
                by_cls.setdefault(cell[1], []).append(c)
        y = f"{y0 + r * ch:.1f}".rstrip("0").rstrip(".")
        for cls, cols in by_cls.items():
            runs, start, prev = [], cols[0], cols[0]
            for c in cols[1:]:
                if c - prev > gap:
                    runs.append((start, prev))
                    start = c
                prev = c
            runs.append((start, prev))
            for a, b in runs:
                s = "".join(row[c][0] if row[c] and row[c][1] == cls else " " for c in range(a, b + 1))
                space = ""
                if s.count(" ") > 10:
                    space = ' xml:space="preserve"'
                else:
                    s = s.replace(" ", "\u00a0")
                length = f' textLength="{num((b - a + 1) * cw)}"' if b > a else ""
                out.setdefault(cls, []).append(f'<text x="{num(x0 + a * cw)}" y="{y}"{length}{space}>{s}</text>')
    return "".join(f'<g class="{cls}">{"".join(texts)}</g>' for cls, texts in out.items())


def rng(seed):
    return random.Random(seed)
