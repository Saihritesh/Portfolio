"""The courtyard's giant tree and clouds, redrawn: a trunk of twisted bark cords that flare into roots,
a spiral knot, forked limbs, moss, hanging vines and glowing fungi; plus procedural moonlit clouds.
Rendered into the courtyard via tools/arena_art.courtyard(tree=..., clouds=...).

Usage:
  python3 tools/tree_art.py preview        -> arena-options/field-<name>.png (+ field-lineup.png)
  python3 tools/tree_art.py write <name>   -> public/assets/rooms/courtyard.png
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
import arena_art as A

RW, RH, FLOOR = A.RW, A.RH, A.FLOOR
BAYER = A.BAYER
fbm, noise, hsh = A.fbm, A.noise, A.hsh

def hx(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)
def pal(*hs): return [hx(h) for h in hs]

def ramp(cols, v, x, y):
    v = max(0.0, min(0.999, v)) * (len(cols) - 1)
    i = int(v); f = v - i
    return cols[min(i + 1, len(cols) - 1)] if f * 16 > BAYER[y % 4][x % 4] else cols[i]

# ----------------------------------------------------------------------------------------- palettes
PALETTES = {
    # cool moonlit slate, like the title-screen tree
    'slate': dict(bark=pal('#04071A', '#0B1430', '#14203F', '#1E2E50', '#2A3E62', '#3A5276', '#506C90', '#7290B0'),
                  moss=pal('#0A1A22', '#12302E', '#1D453A', '#2B5E48'), leaf=pal('#01010E', '#0D172A', '#1E364F', '#2A465E', '#385771', '#516D92'),
                  glow=None, moss_amt=0.25),
    # night-tinted umber: brown bark with blue shadows, moss and teal fungi
    'umber': dict(bark=pal('#05050F', '#120E18', '#211820', '#322326', '#45302C', '#5A3F34', '#715241', '#8E6C55'),
                  moss=pal('#0C1A18', '#15301F', '#224629', '#335E35'), leaf=pal('#020510', '#0B1622', '#142A2E', '#1F3D3A', '#2C5249', '#3E6A57'),
                  glow=pal('#1E6C78', '#4FC6D6', '#B8F4FF'), moss_amt=0.42),
    # closest to the reference: deep brown cords drowned in moss, fungi and vines
    'mossy': dict(bark=pal('#05040C', '#140D12', '#24171A', '#382421', '#4E3329', '#664333', '#7F5740', '#9C7154'),
                  moss=pal('#0B1A14', '#163322', '#23502E', '#34703C', '#4E8E4A'), leaf=pal('#02060E', '#0A1A1C', '#14302A', '#204636', '#2F5E44', '#437852'),
                  glow=pal('#1A6A70', '#3FD0C8', '#C4FFF6'), moss_amt=0.6, vines=True),
    # silver-violet: brighter moonlit bark for contrast against the purple sky
    'silver': dict(bark=pal('#06061A', '#121434', '#1E2148', '#2C2F5E', '#3E4274', '#555A8C', '#7277A6', '#9A9EC4'),
                   moss=pal('#0E1A2A', '#173040', '#22465A', '#2F5E72'), leaf=pal('#03031A', '#0E1230', '#1C2448', '#2A365E', '#3A4A76', '#52648E'),
                   glow=pal('#3A5EB0', '#7FA8FF', '#E0ECFF'), moss_amt=0.2),
}

LIGHT = (0.55, -0.40, 0.73)
WIDE = 1.25                         # trunk girth (1.0 = the first iterations)
TOP = 0.85                          # the upper trunk is 15% more slender than the lower trunk (no bulge under the fork)
LIMB = 1.0                          # branch girth relative to the base sizes
HAZE = 0.32                         # blend toward the night sky: pushes the tree into the distance          # moon: up and to the right of the tree, toward the viewer

# ----------------------------------------------------------------------------------------- strand tubes
def catmull(pts, per=48):
    P = [pts[0]] + pts + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(per):
            t = k / per
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t * t
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t ** 3) for j in range(len(p1))))
    out.append(pts[-1])
    return out

class Tree:
    def __init__(self, px, P, seed=1):
        self.px, self.P, self.seed = px, P, seed
        self.z = {}                                        # (x, y) -> depth already drawn
        self.lit = {}                                      # (x, y) -> (v, up) for moss / glow passes

    def plot(self, x, y, z, v, up=0.0):
        if not (0 <= x < RW and 0 <= y < RH): return
        if self.z.get((x, y), -9) >= z: return
        self.z[(x, y)] = z; self.lit[(x, y)] = (v, up)

    def tube(self, path, strands=12, twist=0.03, base_z=0.0, cord=1.15, seed=0, knots=(), flare=None, squash=1.0):
        """path: [(x, y, r)] (Catmull-Rom'd). Bark cords wind round the tube as helices."""
        S = catmull(path, 64)
        rng = [hsh(i, seed, 91) for i in range(strands)]
        phases = [2 * math.pi * i / strands + (rng[i] - 0.5) * 0.5 for i in range(strands)]
        widths = [0.8 + 0.5 * hsh(i, seed, 92) for i in range(strands)]
        along = 0.0
        for k, (sx, sy, r) in enumerate(S):
            if k: along += math.hypot(sx - S[k - 1][0], sy - S[k - 1][1])
            a0, a1 = S[max(0, k - 1)], S[min(len(S) - 1, k + 1)]
            tx, ty = a1[0] - a0[0], a1[1] - a0[1]; tl = math.hypot(tx, ty) or 1
            nx, ny = ty / tl, -tx / tl                     # screen normal (perpendicular to the path)
            if nx < 0: nx, ny = -nx, -ny                   # +normal points to the right
            # core fill: the deep crevices between cords
            for d in range(-int(r), int(r) + 1):
                self.plot(round(sx + nx * d), round(sy + ny * d * squash), base_z - 1.5, 0.04)
            tw = twist * along + 0.5 * math.sin(along * 0.013 + seed)
            for i in range(strands):
                a = phases[i] + tw
                z = math.cos(a)
                if z < -0.35: continue
                rr = r
                if flare: rr = r + flare(sy, math.sin(a))
                off = rr * math.sin(a)
                cx, cy = sx + nx * off, sy + ny * off * squash
                # knots push the cords aside
                for kx, ky, kr in knots:
                    dx, dy = cx - kx, (cy - ky) * 0.8
                    d = math.hypot(dx, dy)
                    if d < kr * 1.9 and z > 0.2:
                        push = (kr * 1.9 - d) * 0.6
                        cx += dx / (d or 1) * push; cy += dy / (d or 1) * push * 0.5
                hw = max(0.7, math.pi * r / strands * widths[i] * cord * (0.35 + 0.65 * max(0, z)))
                for du in range(-int(hw) - 1, int(hw) + 2):
                    u = du / hw
                    if abs(u) > 1: continue
                    x, y = round(cx + nx * du), round(cy + ny * du * squash)
                    al = a + u * 1.2                          # cord roundness
                    nsx, nsz = math.sin(al), math.cos(al)
                    Nx, Ny, Nz = nx * nsx, ny * nsx, nsz
                    dot = Nx * LIGHT[0] + Ny * LIGHT[1] + Nz * LIGHT[2]
                    v = 0.10 + 0.50 * max(0.0, dot) + 0.05 * z
                    v += (noise(u * 2 + i * 7, along * 0.35, seed + i, 1.0) - 0.5) * 0.16   # fibres along the cord
                    if abs(u) > 0.78: v -= 0.12                                            # cord edge
                    if dot > 0.66 and abs(u) < 0.5: v += 0.07
                    self.plot(x, y, base_z + z + math.sqrt(1 - u * u) * 0.05, v, up=-Ny)

    def knot(self, kx, ky, kr, z=2.0):
        """a spiral whorl in the bark"""
        for y in range(int(ky - kr) - 1, int(ky + kr) + 2):
            for x in range(int(kx - kr) - 1, int(kx + kr) + 2):
                d = math.hypot(x - kx, (y - ky) * 1.15)
                if d > kr: continue
                ang = math.atan2(y - ky, x - kx)
                spiral = math.sin(d * 1.35 - ang * 1.0)
                side = (x - kx) / kr * 0.5 - (y - ky) / kr * 0.3          # lit from the upper right
                v = 0.22 + max(0, spiral) * 0.32 + side * 0.25
                if d < kr * 0.22: v = 0.02
                if d > kr * 0.85: v = 0.3 + side * 0.4                      # raised lip
                self.plot(x, y, z, v)

    def render(self):
        P = self.P; px = self.px; haze = P.get('haze', HAZE); H = hx('#2A2F76')
        for (x, y), (v, up) in self.lit.items():
            v = 0.12 + v * 0.8                               # flatter contrast: further away
            c = ramp(P['bark'], v, x, y)
            m = fbm(x, y, 300 + self.seed, 7)
            if P['moss_amt'] and up > 0.25 and v > 0.08 and m > 1 - P['moss_amt'] * 0.9:
                c = ramp(P['moss'], (v * 0.9 + (m - 0.5) * 0.6), x, y)
            if haze: c = tuple(int(c[j] * (1 - haze) + H[j] * haze) for j in range(3)) + (255,)
            px[x, y] = c

# ----------------------------------------------------------------------------------------- the tree
def make_tree(name, seed=3):
    P = PALETTES[name]
    TX = 82
    def draw(im, px):
        T = Tree(px, P, seed)
        def trunk_flare(y, s):                     # cords splay outward into the root plate
            if y < FLOOR - 28: return 0
            t = (y - (FLOOR - 28)) / 28
            return t ** 2.6 * 22 * WIDE * (0.25 + abs(s) ** 1.5)
        KN = [(70, 112, 9)]
        # limbs first (behind the trunk top)
        L = lambda pts: [(x, y, r * LIMB) for x, y, r in pts]
        T.tube(L([(TX + 2, 96, 24 * WIDE), (TX + 12, 74, 22 * WIDE), (TX + 32, 50, 17 * WIDE), (TX + 58, 30, 13), (TX + 100, 14, 10), (TX + 150, 0, 8), (TX + 190, -14, 7)]),
               strands=8, twist=0.05, base_z=-0.6, seed=seed + 1)
        T.tube(L([(TX - 2, 96, 24 * WIDE), (TX - 10, 70, 22 * WIDE), (TX - 28, 44, 17 * WIDE), (TX - 40, 20, 13), (TX - 52, -6, 11), (TX - 58, -24, 10)]),
               strands=8, twist=-0.05, base_z=-0.5, seed=seed + 2)
        T.tube(L([(TX + 30, 46, 8), (TX + 38, 26, 6), (TX + 36, 8, 5), (TX + 30, -10, 4)]), strands=5, twist=0.08, base_z=-1.0, seed=seed + 3)
        # the trunk: bottom to top so the twist reads as rising
        T.tube([(TX + 2, FLOOR + 3, 33 * WIDE), (TX - 4, 168, 28 * WIDE), (TX + 4, 134, 27 * WIDE), (TX - 3, 104, 28 * WIDE * TOP), (TX + 3, 80, 28 * WIDE * TOP), (TX + 1, 62, 30 * WIDE * TOP)],
               strands=18, twist=0.03, base_z=0.0, seed=seed, knots=KN, flare=trunk_flare)
        T.knot(*KN[0])
        # canopy: heavy leaf masses hanging off the top edge
        LEAF = P['leaf']
        clumps = [(int(-10 + hsh(i, 31) * 250), int(hsh(i, 32) * 16) - 10, 11 + int(hsh(i, 33) * 13)) for i in range(28)]
        clumps += [(-6, 24, 20), (26, 10, 18), (206, -2, 16), (240, -8, 14), (124, -2, 10), (160, 4, 12)]
        canopy = set()
        for cx, cy, r in clumps:
            for y in range(max(0, cy - r), min(RH, cy + r + 1)):
                for x in range(max(0, cx - r - 4), min(RW, cx + r + 5)):
                    dd = math.hypot((x - cx) * 0.8, y - cy) / r
                    edge = fbm(x, y, 11, 4) * 0.45
                    if dd > 0.75 + edge: continue
                    v = 0.22 + 0.36 * ((y - cy) / r) + 0.18 * ((x - cx) / r) + (fbm(x, y, 12, 3) - 0.5) * 0.6
                    if dd > 0.7 + edge * 0.8: v -= 0.25
                    T.z[(x, y)] = 9; canopy.add((x, y))
                    c = ramp(LEAF, v, x, y); Hc = hx('#2A2F76')
                    px[x, y] = tuple(int(c[j] * (1 - HAZE * 0.8) + Hc[j] * HAZE * 0.8) for j in range(3)) + (255,)
        T.lit = {k: v for k, v in T.lit.items() if k not in canopy}
        T.render()
        # hanging vines / moss beards from the limbs
        if P.get('vines') or P['moss_amt'] > 0.3:
            for i in range(14):
                vx = int(TX - 50 + hsh(i, 71) * 190)
                top = None
                for y in range(0, 90):
                    if (vx, y) in T.lit or (vx, y) in canopy: top = y
                if top is None: continue
                L = 8 + int(hsh(i, 72) * 26)
                for k in range(L):
                    x = vx + int(round(math.sin(k * 0.3 + i) * 0.8)); y = top + k
                    if 0 <= y < RH and 0 <= x < RW:
                        px[x, y] = P['moss'][1 + (k % 3 == 0)] if k < L - 1 else P['moss'][-1]
        return after

    def after(im, px):
        # surface roots snaking over the ground, both sides
        roots = [
            [(TX - 34, FLOOR - 3, 9), (TX - 58, FLOOR + 1, 7), (TX - 80, FLOOR + 3, 4.5), (TX - 104, FLOOR + 5, 2.5), (TX - 120, FLOOR + 7, 1.2)],
            [(TX - 20, FLOOR - 1, 7), (TX - 32, FLOOR + 5, 5), (TX - 46, FLOOR + 9, 3), (TX - 58, FLOOR + 12, 1.4)],
            [(TX + 34, FLOOR - 3, 9), (TX + 58, FLOOR + 0, 7), (TX + 84, FLOOR + 2, 4.5), (TX + 108, FLOOR + 4, 2.4), (TX + 126, FLOOR + 6, 1.2)],
            [(TX + 18, FLOOR - 1, 7), (TX + 30, FLOOR + 6, 5), (TX + 44, FLOOR + 10, 3), (TX + 56, FLOOR + 13, 1.4)],
            [(TX - 4, FLOOR, 6), (TX - 8, FLOOR + 6, 4), (TX - 4, FLOOR + 11, 2.4), (TX + 4, FLOOR + 15, 1.2)],
            [(TX - 52, FLOOR + 1, 4), (TX - 64, FLOOR + 8, 3), (TX - 70, FLOOR + 14, 1.6)],
            [(TX + 60, FLOOR + 1, 4), (TX + 72, FLOOR + 8, 3), (TX + 80, FLOOR + 13, 1.4)],
        ]
        R = Tree(px, P, seed + 50)
        for i, rp in enumerate(roots):
            rp = [(TX + (x - TX) * WIDE, y, r * (1 + (WIDE - 1) * 0.6)) for x, y, r in rp]
            R.tube(rp, strands=4, twist=0.06, base_z=0.4, seed=seed + 10 + i, squash=0.55)
        R.render()
        glow_and_motes(px)
        ground_fog(px)

    def glow_and_motes(px):
        # glowing fungi on the trunk and roots
        if P['glow']:
            G = P['glow']
            spots = [(TX - 30, 150, 4), (TX - 27, 146, 3), (TX + 26, 128, 3), (TX - 60, FLOOR + 1, 3), (TX + 70, FLOOR + 2, 2), (TX - 12, 96, 2), (TX + 8, FLOOR + 12, 2)]
            for sx, sy, n in spots:
                for y in range(sy - 7, sy + 8):                                   # soft dithered halo
                    for x in range(sx - 8, sx + 9):
                        if 0 <= x < RW and 0 <= y < RH and math.hypot(x - sx, y - sy) < 7 and (x + y) % 2 == 0 and hsh(x, y, 77) > 0.45:
                            c = px[x, y]
                            px[x, y] = tuple(min(255, int(c[j] * 0.6 + G[0][j] * 0.4)) for j in range(3)) + (255,)
                for k in range(n):                                                 # little shelf caps
                    x = sx - n + 2 * k; y = sy - (k % 2)
                    if 0 <= x < RW and 0 <= y < RH:
                        px[x, y] = G[1]; px[min(RW - 1, x + 1), y] = G[1]
                        if y - 1 >= 0: px[x, y - 1] = G[2]
        # fireflies-ish motes near the roots
        for i in range(10):
            x = int(TX - 70 + hsh(i, 81) * 150); y = int(FLOOR - 40 + hsh(i, 82) * 36)
            if 0 <= x < RW and 0 <= y < RH: px[x, y] = (P['glow'] or [None, hx('#FFC872')])[1]
    return draw

# ----------------------------------------------------------------------------------------- foreground haze
FOG = 0.95                         # strength of the low ground mist
def ground_fog(px):
    """a low, drifting mist band hugging the ground: thickest at the grass line, thinning upward and toward the viewer"""
    mist = [hx('#2A2F76'), hx('#3D3680'), hx('#5A52A0')]
    for y in range(150, RH):
        for x in range(RW):
            band = math.exp(-((y - 194) / 13.0) ** 2)                       # hugs the ground line
            n = fbm(x * 0.35, y * 1.6, 500, 10)                              # long horizontal wisps
            a = band * (0.35 + 0.9 * n) * FOG
            if a <= 0.05: continue
            # ordered dither so the mist stays pixel-crisp
            if a * 16 < BAYER[y % 4][x % 4] + 1: continue
            c = px[x, y]
            m = mist[min(2, int(n * 3))]
            k = min(0.6, 0.3 + a * 0.45)
            px[x, y] = tuple(int(c[j] * (1 - k) + m[j] * k) for j in range(3)) + (255,)

# ----------------------------------------------------------------------------------------- clouds
SKYC = pal('#020727', '#060C2B', '#1D174F', '#241F5E', '#2A2F76', '#3D3680', '#5A52A0', '#8A84C4', '#C9C6D8')
MX, MY = 178, 52

def cloud_layer(px, density, rim=True):
    """density(x, y) -> 0..1. Lit from the moon: tops and moon-facing edges bright, bellies dark."""
    for y in range(0, 170):
        for x in range(RW):
            if math.hypot(x - MX, y - MY) < 13: continue           # keep the moon clear
            d = density(x, y)
            if d <= 0.0: continue
            above = density(x, y - 2); below = density(x, y + 2)
            toward = density(x + (1 if x < MX else -1) * 2, y - 1)
            v = 0.36 + d * 0.26
            if rim and above < 0.08: v += 0.26                    # silver lining on top edges
            if toward < d - 0.05: v += 0.12
            if below < 0.05: v -= 0.12                            # flat dark bellies
            dm = math.hypot(x - MX, y - MY)
            v += max(0, 0.3 - dm / 220)                           # brighter near the moon
            if d < 0.18 and (x + y) % 2: continue                 # feathered edges
            px[x, y] = ramp(SKYC, v, x, y)

def clouds_wisps(im, px):
    def D(x, y):
        bands = [(64, 7, 0.0), (92, 5, 2.0), (118, 6, 4.0), (34, 4, 6.0)]
        best = 0
        for yc, h, s in bands:
            yy = yc + 6 * math.sin(x * 0.012 + s)
            e = math.exp(-((y - yy) / h) ** 2)
            n = noise(x * 0.25 + s * 40, y * 1.4, 400 + int(s), 6)
            best = max(best, e * (n * 1.6 - 0.55))
        return best
    cloud_layer(px, D)

def clouds_banks(im, px):
    puffs = [(10, 116, 20), (40, 106, 24), (70, 98, 26), (100, 108, 20), (130, 116, 16), (232, 100, 22), (262, 88, 28), (296, 96, 24), (328, 106, 20), (352, 114, 16),
             (120, 58, 13), (142, 64, 11), (214, 32, 12), (232, 26, 15), (252, 34, 10)]
    def D(x, y):
        best = 0
        for cx, cy, r in puffs:
            if y > cy + r * 0.35: continue                         # flat bottoms
            d = math.hypot((x - cx) * 0.75, y - cy) / r
            best = max(best, 1 - d + (fbm(x, y, 410, 5) - 0.5) * 0.5)
        return best
    cloud_layer(px, D)

def clouds_veil(im, px):
    """a long moonlit veil crossing below the moon, plus a few high streaks"""
    def D(x, y):
        yy = 74 + 10 * math.sin(x * 0.01 + 1.2) + 4 * math.sin(x * 0.05)
        e = math.exp(-((y - yy) / 9) ** 2)
        n = fbm(x * 0.6, y * 1.6, 420, 8)
        band = e * (n * 1.8 - 0.6)
        hi = math.exp(-((y - 26 - 0.04 * x) / 3) ** 2) * (noise(x * 0.3, y, 421, 5) * 1.6 - 0.7)
        low = math.exp(-((y - 128) / 6) ** 2) * (noise(x * 0.4, y * 1.5, 422, 6) * 1.7 - 0.8)
        return max(band, hi, low)
    cloud_layer(px, D)

VERSIONS = {
    'v1-slate-wisps': ('slate', clouds_wisps),
    'v2-umber-banks': ('umber', clouds_banks),
    'v3-mossy-veil': ('mossy', clouds_veil),
    'v4-silver-banks': ('silver', clouds_banks),
}

def no_clouds(im, px): pass

def cloud_sprite(seed, w, h, n):
    """a free-floating moonlit cloud on a transparent canvas (drifts across the sky layer in-game)"""
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); px = im.load()
    puffs = []
    for i in range(n):
        r = h * (0.28 + 0.22 * hsh(i, seed, 601))
        cx = r + (w - 2 * r) * (i + 0.5) / n + (hsh(i, seed, 602) - 0.5) * 6
        cy = h * 0.62 - r * 0.25 - hsh(i, seed, 603) * r * 0.5
        puffs.append((cx, cy, r))
    base = h * 0.78
    def D(x, y):
        if y > base: return 0
        best = 0
        for cx, cy, r in puffs:
            d = math.hypot((x - cx) * 0.8, y - cy) / r
            best = max(best, 1 - d + (fbm(x, y, 610 + seed, 4) - 0.5) * 0.45)
        return best
    for y in range(h):
        for x in range(w):
            d = D(x, y)
            if d <= 0: continue
            if d < 0.16 and (x + y) % 2: continue                       # feathered, dithered edge
            v = 0.40 + d * 0.30 - (y / h) * 0.18                          # lighter toward the top of the cloud
            if D(x, y - 2) <= 0.06: v += 0.32                             # moonlit top
            elif D(x, y - 4) <= 0.06: v += 0.14
            if D(x, y + 2) <= 0.04: v -= 0.16                             # dark flat belly
            px[x, y] = ramp(SKYC, v, x, y)
    return im

CLOUDS = [(1, 84, 26, 5), (2, 120, 32, 6), (3, 60, 20, 4), (4, 100, 28, 5), (5, 70, 22, 4)]

def write(name):
    """courtyard.png (flat fallback), courtyard_sky.png (clear sky + moon), courtyard_fg.png (sky cut out),
    and cloud_<n>.png sprites that drift between them."""
    tree, _ = VERSIONS[name]
    full = A.courtyard('C', tree=make_tree(tree), clouds=no_clouds)
    sky = A.courtyard('C', sky_only=True)
    fg = full.copy(); pf, ps = fg.load(), sky.load()
    for y in range(RH):
        for x in range(RW):
            if pf[x, y] == ps[x, y]: pf[x, y] = (0, 0, 0, 0)
    sky.save('public/assets/rooms/courtyard_sky.png')
    fg.save('public/assets/rooms/courtyard_fg.png')
    for i, (seed, w, h, n) in enumerate(CLOUDS):
        cloud_sprite(seed, w, h, n).save(f'public/assets/sprites/cloud_{i + 1}.png')

def field(name):
    tree, clouds = VERSIONS[name]
    return A.courtyard('C', tree=make_tree(tree), clouds=clouds)

if __name__ == '__main__':
    os.makedirs('arena-options', exist_ok=True)
    if sys.argv[1] == 'preview':
        names = sys.argv[2:] or list(VERSIONS)
        ims = []
        for n in names:
            im = field(n); ims.append(im)
            im.resize((RW * 4, RH * 4), Image.NEAREST).save(f'arena-options/field-{n}.png')
        cols = 2; S = 2
        out = Image.new('RGBA', (cols * (RW * S + 8), ((len(ims) + 1) // 2) * (RH * S + 8)), (0, 0, 0, 255))
        for i, im in enumerate(ims):
            out.paste(im.resize((RW * S, RH * S), Image.NEAREST), ((i % cols) * (RW * S + 8), (i // cols) * (RH * S + 8)))
        out.save('arena-options/field-lineup.png')
    else:
        write(sys.argv[2])
