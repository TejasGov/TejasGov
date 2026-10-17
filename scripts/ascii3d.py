"""Tiny software renderers that draw 3D scenes into character grids.

Every renderer returns rows of (char, class) cells for kit.ascii_runs. Screen
space is measured in pixels so the character cell's aspect ratio is honoured.
"""

import math

import numpy as np

# dark → bright
RAMP_SOLID = " .,-~:;=!*#$@"
RAMP_FACE = " .,-~:;=!*#$@"
RAMP_GLOW = " .'`,:;-~=+*"


def _grid(cols, rows, cw, ch, cx, cy):
    """Pixel offsets of each cell centre from (cx, cy)."""
    xs = (np.arange(cols) + 0.5) * cw - cx
    ys = (np.arange(rows) + 0.5) * ch - cy
    return np.meshgrid(xs, ys)


def _pick(ramp, v):
    idx = np.clip((v * (len(ramp) - 1)).round().astype(int), 0, len(ramp) - 1)
    return np.array(list(ramp))[idx]


def _rotation(axis, angle):
    axis = np.asarray(axis, float)
    axis /= np.linalg.norm(axis)
    x, y, z = axis
    c, s = math.cos(angle), math.sin(angle)
    C = 1 - c
    return np.array([
        [c + x * x * C, x * y * C - z * s, x * z * C + y * s],
        [y * x * C + z * s, c + y * y * C, y * z * C - x * s],
        [z * x * C - y * s, z * y * C + x * s, c + z * z * C],
    ])


# ── moon ────────────────────────────────────────────────────────────────────
class Moon:
    """A procedurally cratered sphere: smooth maria, a few hundred craters."""

    def __init__(self, seed=7, craters=90):
        r = np.random.default_rng(seed)
        self.waves = [(self._unit(r), r.uniform(1.5, 7), r.uniform(0, 6.3), a)
                      for a in np.linspace(0.32, 0.05, 14)]
        self.maria = [(self._unit(r), r.uniform(1.0, 2.2), r.uniform(0, 6.3)) for _ in range(5)]
        self.craters = [(self._unit(r), r.uniform(0.05, 0.11) if i > 12 else r.uniform(0.13, 0.24))
                        for i in range(craters)]

    @staticmethod
    def _unit(r):
        v = r.normal(size=3)
        return v / np.linalg.norm(v)

    def albedo(self, p):
        """p: (..., 3) unit vectors in the moon's own frame → albedo in 0..1."""
        a = np.full(p.shape[:-1], 0.62)
        for d, f, phase, amp in self.waves:
            a += amp * 0.35 * np.sin(f * (p @ d) * 2.2 + phase)
        m = sum(np.sin(f * (p @ d) * 2 + ph) for d, f, ph in self.maria) / len(self.maria)
        a -= 0.28 * np.clip(m * 2.2, 0, 1)
        for c, radius in self.craters:
            d = np.arccos(np.clip(p @ c, -1, 1)) / radius
            a -= 0.22 * np.clip(1 - d / 0.85, 0, 1) ** 0.6 * (d < 0.85)
            a += 0.30 * np.exp(-((d - 0.97) / 0.12) ** 2)
        return np.clip(a, 0, 1)


def moon_frame(moon, angle, cols, rows, cw, ch, cx, cy, radius, tilt=0.38, sun=(0.62, 0.78, -0.62)):
    """The moon turned by `angle`: earthshine on the near side, and a thin
    crescent where the sun, almost directly behind it, grazes the limb."""
    X, Y = _grid(cols, rows, cw, ch, cx, cy)
    nx, ny = X / radius, Y / radius
    rr = nx * nx + ny * ny
    inside = rr < 0.975
    nz = np.sqrt(np.clip(1 - rr, 0, 1))
    p = np.stack([nx, -ny, nz], -1)
    axis = (math.sin(tilt), math.cos(tilt), 0.0)
    obj = p @ _rotation(axis, angle)
    albedo = moon.albedo(obj)
    s = np.array(sun) / np.linalg.norm(sun)
    lit = np.clip(p @ s, 0, 1) ** 0.8
    earth = albedo * (0.34 + 0.66 * nz ** 0.6)
    chars_e = _pick(RAMP_FACE, np.clip((earth - 0.08) * 1.05, 0, 1))
    chars_l = _pick(RAMP_FACE, np.clip(0.35 + albedo * lit * 1.6, 0, 1))
    out = []
    for r in range(rows):
        row = []
        for c in range(cols):
            if not inside[r, c]:
                row.append(None)
            elif lit[r, c] > 0.14:
                row.append((chars_l[r, c], "l"))
            else:
                row.append((chars_e[r, c], "m"))
        out.append(row)
    return out


def _ray_glyph(theta):
    """A stroke that points along the radius: - \\ | /  (screen y grows down)."""
    a = np.mod(theta, np.pi)
    return np.where((a < np.pi / 8) | (a > 7 * np.pi / 8), "-",
           np.where(a < 3 * np.pi / 8, "\\", np.where(a < 5 * np.pi / 8, "|", "/")))


def corona(cols, rows, cw, ch, cx, cy, radius, seed=3, sun=(0.62, -0.78), drift=0.0, sparkle=0, spread=1.0):
    """The corona as a brightness field: a tight white halo, broad helmet
    streamers and fine filaments, shaded with a density ramp. Faint cells are
    dithered out so the glow thins into the dark instead of stopping at an edge."""
    r = np.random.default_rng(seed)
    X, Y = _grid(cols, rows, cw, ch, cx, cy)
    rho = np.hypot(X, Y) / radius
    theta = np.arctan2(Y, X)
    toward_sun = np.cos(theta - math.atan2(sun[1], sun[0]))

    fine = sum(np.cos(k * theta + r.uniform(0, 6.3) + drift * 0.18) * r.uniform(0.5, 1.0)
               for k in (11, 17, 23, 31, 43, 57)) / 3.2
    helmets = sum(np.exp(-((np.angle(np.exp(1j * (theta - a)))) / w) ** 2) * s
                  for a, w, s in ((-2.65, 0.32, 1.0), (-0.45, 0.26, 0.8), (0.5, 0.36, 1.0),
                                  (2.35, 0.3, 0.8), (1.6, 0.16, 0.35), (-1.5, 0.14, 0.3)))
    filaments = np.clip(fine, 0, None) ** 2

    halo = np.exp(-(rho - 1) / (0.13 * spread))
    streamers = np.exp(-(rho - 1) / (0.62 * spread)) * helmets * (0.75 + 0.25 * fine)
    rays = np.exp(-(rho - 1) / (0.32 * spread)) * filaments * 0.45
    glow = np.where(rho > 1.035, 0.95 * halo + 0.62 * streamers + rays, 0)
    glow *= 0.8 + 0.4 * np.clip(toward_sun, 0, 1)

    ring = np.exp(-((rho - 1.0) / 0.028) ** 2) * (0.3 + 0.7 * np.clip(toward_sun, 0, 1) ** 3)
    bead = np.exp(-(((X / radius) - sun[0] * 1.01) ** 2 + ((Y / radius) - sun[1] * 1.01) ** 2) / 0.006)
    dither = np.random.default_rng(seed * 101 + sparkle).random(rho.shape)
    ramp = " .`'-:;=+*#"

    out = []
    for i in range(rows):
        row = []
        for j in range(cols):
            g, k, b = glow[i, j], ring[i, j], bead[i, j]
            if b > 0.2:
                row.append(("@" if b > 0.75 else "#" if b > 0.45 else "*", "w"))
            elif k > 0.3 and 0.975 < rho[i, j] < 1.05:
                row.append(("#" if k > 0.85 else "*" if k > 0.6 else "+" if k > 0.42 else ":", "w" if k > 0.85 else "h"))
            elif g > 0.025 and dither[i, j] < min(1.0, g * 3.2):
                v = min(g, 1.0)
                ch_ = ramp[max(1, min(len(ramp) - 1, int(v * len(ramp) * 1.15)))]
                cls = "w" if v > 0.82 else "h" if v > 0.55 else "s" if v > 0.3 else "e" if v > 0.14 else "d"
                row.append((ch_, cls))
            else:
                row.append(None)
        out.append(row)
    return out


# ── polyhedra ───────────────────────────────────────────────────────────────
def dodecahedron_planes():
    """Face normals of a regular dodecahedron (the icosahedron's vertices)."""
    phi = (1 + 5 ** 0.5) / 2
    v = []
    for a in (-1, 1):
        for b in (-phi, phi):
            v += [(0, b, a), (b, a, 0), (a, 0, b)]
    v = np.array(v, float)
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def solid_frame(normals, rot, cols, rows, cw, ch, cx, cy, radius, light=(-0.45, 0.62, 0.64), cls_fn=None):
    """Orthographic ray cast into a convex solid given by unit face normals and
    a common inradius; flat shading, with face edges picked out."""
    X, Y = _grid(cols, rows, cw, ch, cx, cy)
    n = normals @ rot.T
    ox, oy = X / radius, -Y / radius
    # ray: (ox, oy, z), z from +inf toward -inf; half-space n·p <= inr
    inr = 0.795
    d = -n[:, 2]                        # n·dir with dir = (0,0,-1)
    s = n[:, 0, None, None] * ox + n[:, 1, None, None] * oy
    # n·(o + t·dir) <= inr, o.z = 0 →  s + t*d <= inr
    t = (inr - s) / d[:, None, None]
    enter = np.where(d[:, None, None] < 0, t, -np.inf)
    leave = np.where(d[:, None, None] > 0, t, np.inf)
    t_in, t_out = enter.max(0), leave.min(0)
    hit = t_in < t_out
    face = enter.argmax(0)
    second = np.sort(enter, 0)[-2]
    edge = (t_in - second) < 0.05
    L = np.array(light) / np.linalg.norm(light)
    lum = np.clip(n[face] @ L, 0, 1)
    lum = 0.12 + 0.88 * lum
    chars = _pick(RAMP_SOLID, lum)
    rows_out = []
    for i in range(rows):
        row = []
        for j in range(cols):
            if not hit[i, j]:
                row.append(None)
            elif edge[i, j]:
                row.append(("#" if lum[i, j] > 0.5 else "+", "k"))
            else:
                row.append((chars[i, j], cls_fn(lum[i, j]) if cls_fn else "f"))
        rows_out.append(row)
    return rows_out


def spin(frame, frames, axis=(0.35, 1.0, 0.18), base=None):
    r = _rotation(axis, 2 * math.pi * frame / frames)
    return r @ base if base is not None else r


def dodecahedron():
    """Vertices, edges and face normals of a regular dodecahedron (circumradius 1)."""
    phi = (1 + 5 ** 0.5) / 2
    v = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    for a in (-1 / phi, 1 / phi):
        for b in (-phi, phi):
            v += [(0, a, b), (a, b, 0), (b, 0, a)]
    v = np.array(v, float) / math.sqrt(3)
    d = np.linalg.norm(v[:, None] - v[None], axis=-1)
    edge = d[d > 1e-6].min()
    edges = [(i, j) for i in range(len(v)) for j in range(i + 1, len(v)) if abs(d[i, j] - edge) < 1e-6]
    return v, edges, dodecahedron_planes()


def wire_frame(solid, rot, cols, rows, cw, ch, cx, cy, radius):
    """ASCII wireframe: strokes follow each edge's on-screen slope, hidden edges
    are dotted, vertices are marked."""
    verts, edges, normals = solid
    v = verts @ rot.T
    n = normals @ rot.T
    inr = (verts @ normals[0]).max()
    on_face = np.abs(v @ n.T - inr) < 1e-6          # vertex × face
    px = cx + v[:, 0] * radius
    py = cy - v[:, 1] * radius
    grid = [[None] * cols for _ in range(rows)]
    rank = [[-1] * cols for _ in range(rows)]

    def put(x, y, cell, level):
        c, r = int(x // cw), int(y // ch)
        if 0 <= c < cols and 0 <= r < rows and level >= rank[r][c]:
            grid[r][c], rank[r][c] = cell, level

    order = sorted(edges, key=lambda e: v[e[0], 2] + v[e[1], 2])
    for i, j in order:
        faces = on_face[i] & on_face[j]
        front = (n[faces, 2] > 0).any()
        dx, dy = px[j] - px[i], py[j] - py[i]
        a = math.atan2(dy, dx) % math.pi
        glyph = "-" if a < math.pi / 8 or a > 7 * math.pi / 8 else "\\" if a < 3 * math.pi / 8 else "|" if a < 5 * math.pi / 8 else "/"
        steps = int(max(abs(dx) / cw, abs(dy) / ch) * 3) + 1
        for t in np.linspace(0, 1, steps):
            if front:
                put(px[i] + dx * t, py[i] + dy * t, (glyph, "f"), 2)
            else:
                put(px[i] + dx * t, py[i] + dy * t, (".", "b"), 1)
    for k in np.argsort(v[:, 2]):
        front = (n[on_face[k], 2] > 0).any()
        put(px[k], py[k], ("@" if front else "o", "k" if front else "b"), 3 if front else 1)
    return grid
