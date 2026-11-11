"""Courtyard mini-game art: background, ogre, dragon, fireball, hearts.

Usage:
  python3 tools/arena_art.py preview   # sheets + a full mock-up screen -> arena-options/ (game untouched)
  python3 tools/arena_art.py write     # write game assets to public/assets/{rooms,sprites}/

All art is native-resolution pixel art in the Knight for Hire palette, shown at 4x.
"""
import math, os, sys
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RW, RH, FLOOR = 360, 225, 196

def hx(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)
C = {k: hx(v) for k, v in dict(
    void='#05070F', K='#0A0C16', mort='#080A18', b1='#11162C', b2='#161C3A', b3='#1D254A', b4='#28325E',
    f1='#1C2036', f2='#262C48', f3='#3A4266', p1='#232A4A', p2='#343E66', p3='#4C5888', p4='#6C78A8',
    sky0='#0B1330', sky1='#162452', sky2='#24387A', star='#E6F0FF', moon='#F2EAD3', moon2='#C9C2B0',
    w0='#2A1A12', w1='#4A2E1C', w2='#6E4628', w3='#94643A',
    g1='#966216', g2='#D6962E', g3='#FFD27A',
    r0='#3A121C', r1='#6A2434', r2='#94384C', r3='#B85A6A',
    fl0='#B8641E', fl1='#E89A3C', fl2='#FFC872', fl3='#FFF3C4',
    iron1='#3A4058', iron2='#6A7290', bone='#D9D2C3', bone2='#A89F8C',
    moss0='#0F2018', moss='#1F3A30', moss2='#2C5A45', moss3='#3E7A5A',
    o0='#22341A', o1='#3A5626', o2='#587E34', o3='#82A64A', eye='#FF6A3A',
    heart='#D04A5E', heart2='#F28A96', heartd='#3A2030',
).items()}

def hsh(x, y, s=0):
    v = math.sin(x * 12.9898 + y * 78.233 + s * 37.719) * 43758.5453
    return v - math.floor(v)

def outline(im, col=C['K'], skip=()):
    """1px dark outline around every opaque pixel (skips pixels whose colour is in skip)."""
    px = im.load(); w, h = im.size
    out = im.copy(); po = out.load()
    for y in range(h):
        for x in range(w):
            if px[x, y][3]: continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < w and 0 <= yy < h and px[xx, yy][3] and px[xx, yy] not in skip:
                    po[x, y] = col; break
    return out

def mirror(im): return im.transpose(Image.FLIP_LEFT_RIGHT)

# =============================================================== background
# ---- palette sampled from the title screen (public/assets/intro/*.png)
IN = {k: hx(v) for k, v in dict(
    sk0='#020727', sk1='#060C2B', sk2='#1D174F', sk3='#241F5E', sk4='#2A2F76', sk5='#3D3680',
    moon='#F6F3E8', moon2='#C9C6D8',
    bk0='#020827', bk1='#0E1C3A', bk2='#1A2B4D', bk3='#263D58', bk4='#32446D', bk5='#385771', bk6='#495B89', bk7='#516D92', bk8='#738FAF',
    lf0='#01010E', lf1='#0D172A', lf2='#1E364F', lf3='#2A465E', lf4='#385771', lf5='#516D92',
    cs0='#02010E', cs1='#0F0E19', cs2='#1A1934', cs3='#1F235E', cs4='#3D3680',
    win0='#B8641E', win1='#E89A3C', win2='#FFC872', win3='#FFF3C4',
    gr0='#020517', gr1='#0D172A', gr2='#0E1C3A', gr3='#1A2B4D', gr4='#263D58',
).items()}
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]

def noise(x, y, s=0, sc=8.0):
    """Smooth value noise in [0,1]."""
    x, y = x / sc, y / sc
    x0, y0 = math.floor(x), math.floor(y); fx, fy = x - x0, y - y0
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b = hsh(x0, y0, s), hsh(x0 + 1, y0, s); c, d2 = hsh(x0, y0 + 1, s), hsh(x0 + 1, y0 + 1, s)
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d2 * fx) * fy

def fbm(x, y, s=0, sc=16.0):
    return 0.55 * noise(x, y, s, sc) + 0.3 * noise(x, y, s + 7, sc / 2) + 0.15 * noise(x, y, s + 13, sc / 4)

def ramp(names, v, x, y):
    """Pick from a colour ramp by v in [0,1], with ordered dithering between steps."""
    v = max(0.0, min(0.999, v)) * (len(names) - 1)
    i = int(v); f = v - i
    j = min(i + 1, len(names) - 1)
    return IN[names[j]] if f * 16 > BAYER[y % 4][x % 4] else IN[names[i]]

SKY = ['sk0', 'sk1', 'sk2', 'sk3', 'sk4', 'sk5']
BARK = ['bk0', 'bk1', 'bk2', 'bk3', 'bk4', 'bk5', 'bk6', 'bk7']
LEAF = ['lf0', 'lf1', 'lf2', 'lf3', 'lf4', 'lf5']
GROUND = ['gr0', 'gr1', 'gr2', 'gr3', 'gr4']

# ---------------------------------------------------------------- castle pieces (title-screen style)
STONE = ['cs0', 'cs1', 'cs2', 'cs3']
def stone(x, y, v, haze=0.0):
    """Streaky dark stone like the title-screen castle: vertical grain, faint courses."""
    streak = noise(x, y * 0.16, 51, 1.6)
    val = v + (streak - 0.5) * 0.32 + (fbm(x, y, 52, 6) - 0.5) * 0.14
    if y % 9 == 0 and hsh(x // 7, y // 9, 53) > 0.35: val -= 0.14
    if haze > 0:                                                # distance: lift toward the sky colours
        return ramp(['cs0', 'cs1', 'sk1', 'sk2', 'sk3'], val * (1 - haze) + haze * 0.75, x, y)
    return ramp(STONE, val, x, y)

def pinnacles(px, x0, x1, top, haze, tall=8):
    """Spiky gothic pinnacles along a roofline, corners tallest."""
    xs = [x0 + 1, x1 - 2] + list(range(x0 + 5, x1 - 4, 5))
    for i, sx in enumerate(xs):
        h = tall if i < 2 else 3 + int(hsh(sx, top, 54) * (tall - 3))
        for k in range(h):
            y = top - h + k
            wdt = 1 if k < h * 0.45 else 2
            for x in range(sx, sx + wdt):
                if 0 <= x < RW and 0 <= y < RH: px[x, y] = stone(x, y, 0.25, haze) if x > sx else IN['cs3']
        for x in range(x0, x1): px[x, top] = IN['cs3'] if (x + top) % 2 else IN['cs2']

def lancet(px, x, y, h, w=2):
    for yy in range(y - 1, y + h + 1):
        for xx in range(x - 1, x + w + 1):
            if 0 <= xx < RW and 0 <= yy < RH: px[xx, yy] = IN['bk4']     # slate frame like the title screen
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            px[xx, yy] = IN['win1'] if yy < y + h * 0.55 else IN['win0']
    px[x, y] = IN['win2']

def keep_stepped(px):
    """A: tiers stepping up toward us and merging into the gate wall (one stacked keep)."""
    tiers = [(144, 176, 134), (168, 200, 110), (192, 224, 86), (214, 240, 60), (232, 252, 34)]
    for x0, x1, top in tiers:
        haze = max(0.0, (236 - x0) / 92) * 0.55
        for y in range(top, FLOOR):
            for x in range(x0, x1):
                px[x, y] = stone(x, y, 0.3, haze)
            px[x0, y] = IN['cs3'] if y % 2 else stone(x0, y, 0.4, haze)          # moonlit left edge
        pinnacles(px, x0, x1, top, haze, 7 + (x1 - x0) // 6)
    # the tallest needle spire, like the title-screen castle's
    for k in range(44):
        half = k / 44 * 4
        for x in range(int(226 - half), int(226 + half) + 1):
            px[x, 16 + k] = IN['cs3'] if x == int(226 - half) else stone(x, 16 + k, 0.25, 0.15)
    for x, y, h in ((152, 150, 6), (176, 126, 7), (186, 150, 6), (200, 104, 8), (210, 136, 7), (221, 80, 8), (238, 56, 9), (244, 100, 8)):
        lancet(px, x, y, h)

def keep_wing(px):
    """C: the gate wall turns a corner and its side wall recedes into the distance in perspective."""
    X0, X1 = 166, 250                                           # far end .. near corner
    def top(x): return 104 - (x - X0) / (X1 - X0) * 118
    def bot(x): return 178 + (x - X0) / (X1 - X0) * 18
    for x in range(X0, X1):
        t = (x - X0) / (X1 - X0); ty, by = top(x), bot(x)
        haze = (1 - t) ** 1.6 * 0.42                            # smooth fade into the night with distance
        for y in range(max(0, int(ty)), int(by)):
            k = (y - ty) / (by - ty)
            v = 0.33 + 0.03 * (1 - t)                           # matches the gate wall where they meet
            c = stone(x, y, v, haze)
            if int(k * 16) != int((k - 1 / max(1, by - ty)) * 16): c = IN['cs0']          # courses converge
            px[x, y] = c
        # battlements along the receding top edge
        if int(t * 18) % 2 == 0:
            for y in range(int(ty) - 3, int(ty)):
                if y >= 0: px[x, y] = stone(x, y, 0.3, haze)
        if int(ty) - 3 >= 0: px[x, max(0, int(ty) - 3 if int(t * 18) % 2 == 0 else int(ty))] = IN['cs3']
    # windows shrink and crowd together with distance
    for t in (0.08, 0.26, 0.47, 0.72):
        x = int(X0 + t * (X1 - X0)); hgt = bot(x) - top(x)
        w = max(1, round(hgt / 40)); h = max(3, round(hgt / 9))
        for k in (0.3, 0.62):
            lancet(px, x, int(top(x) + hgt * k), h, w)
    # the far end tower, which we can see the top of, with a needle spire
    for y in range(70, 180):
        for x in range(150, 168):
            px[x, y] = stone(x, y, 0.33, 0.42)
        px[150, y] = IN['cs3'] if y % 2 else px[150, y]
    pinnacles(px, 150, 168, 70, 0.42, 8)
    for k in range(34):
        half = k / 34 * 4
        for x in range(int(159 - half), int(159 + half) + 1):
            px[x, 36 + k] = IN['cs3'] if x == int(159 - half) else stone(x, 36 + k, 0.3, 0.42)
    lancet(px, 156, 96, 7); lancet(px, 160, 132, 6)


def courtyard(castle='C', tree=None, clouds=None, sky_only=False):
    """Right outside the castle gate, under the giant tree from the title screen.
    Close up, so the castle and the tree rise past the top of the frame. Light comes
    from the moon (upper middle), so moonlit edges face it; everything recedes
    into purple haze with distance (atmospheric perspective)."""
    im = Image.new('RGBA', (RW, RH), IN['sk0']); px = im.load()
    MX, MY = 178, 52                                            # moon

    # ---------------- sky: vertical ramp, brighter near the horizon and around the moon
    for y in range(FLOOR):
        for x in range(RW):
            v = 0.08 + (y / FLOOR) ** 1.4 * 0.72
            dm = math.hypot(x - MX, y - MY)
            v += max(0, 0.32 - dm / 260)
            px[x, y] = ramp(SKY, v, x, y)
            if y < 140 and hsh(x, y, 3) > 0.995 and dm > 26: px[x, y] = IN['moon2'] if hsh(x, y, 4) > 0.5 else IN['sk5']
    # moon: halo rings like the title screen, then the disc with craters
    for y in range(MY - 22, MY + 23):
        for x in range(MX - 22, MX + 23):
            dm = math.hypot(x - MX, y - MY)
            if dm < 15: px[x, y] = IN['sk5'] if dm >= 12 else px[x, y]
            elif dm < 19 and (x + y) % 2 == 0: px[x, y] = IN['sk4']
    for y in range(MY - 11, MY + 12):
        for x in range(MX - 11, MX + 12):
            dm = math.hypot(x - MX, y - MY)
            if dm <= 10.5: px[x, y] = IN['moon2'] if dm > 9.6 else IN['moon']
    for cx, cy in ((-3, -2), (-2, -2), (-3, -1), (4, 3), (5, 3), (4, 4), (2, -6), (-5, 5)):
        px[MX + cx, MY + cy] = IN['moon2']
    if sky_only: return im                                      # the back layer, for drifting cloud sprites

    # clouds lifted straight from the title screen's cloud layer
    if clouds: clouds(im, px)                                    # swappable (tools/tree_art.py)


    # ---------------- far hills + forest silhouettes (hazy purple: far = lighter, less contrast)
    for x in range(RW):
        h1 = 150 + 7 * math.sin(x * 0.025 + 1) + 4 * math.sin(x * 0.09)
        h2 = 166 + 5 * math.sin(x * 0.04 + 3) + 3 * fbm(x, 0, 9, 6) * 6
        for y in range(int(h1), FLOOR): px[x, y] = ramp(['sk2', 'sk3'], 0.55 - (y - h1) / 60, x, y)
        for y in range(int(h2), FLOOR): px[x, y] = ramp(['sk0', 'sk1', 'sk2'], 0.5 - (y - h2) / 40, x, y)
    for i in range(70):                                         # pine tips poking above the near forest
        tx = int(i * 5.3 + hsh(i, 1) * 4); th = 6 + int(hsh(i, 2) * 10); base = 170
        for k in range(th):
            half = int((k / th) * 3)
            for xx in range(tx - half, tx + half + 1):
                if 0 <= xx < RW: px[xx, base - th + k] = IN['sk1']

    # ---------------- the castle behind: one stone mass in the title screen's style
    if castle == 'A': keep_stepped(px)
    else: keep_wing(px)

    after = None
    if tree: after = tree(im, px)                                # swappable (tools/tree_art.py); may return a post-ground pass
    else:
        # ---------------- the giant tree: wide root flare, then a trunk of even thickness
        TX = 80
        FLARE = 30
        def center(y): return TX + 4 * math.sin(y * 0.02)
        def half_w(y):
            if y > FLOOR - FLARE:
                t = (y - (FLOOR - FLARE)) / FLARE
                return 30 + t ** 2 * 64
            return 30
        KNOTS = [(70, 120, 9), (93, 62, 7), (64, 168, 6)]
        for y in range(0, FLOOR + 2):
            c, hw = center(y), half_w(y)
            for x in range(int(c - hw) - 1, int(c + hw) + 2):
                if not (0 <= x < RW): continue
                u = (x - c) / hw
                if abs(u) > 1: continue
                if y > FLOOR - 16 and abs(u) > 0.55:                # gaps between the outer roots
                    if math.sin((x - c) * 0.17 + 1.3) < -0.55 + (y - (FLOOR - 16)) / 24: continue
                # coiling bark: strands wrap the trunk as a helix (theta round the trunk, rising with y)
                uu = max(-1.0, min(1.0, (x - c) / 30))              # use the trunk radius, so strands run into the roots
                theta = math.asin(uu)
                ridge = math.sin(6 * (theta + y * 0.085) + fbm(x, y, 2, 9) * 2.5)
                for kx, ky, kr in KNOTS:                             # whorls: the grain spirals round each knot
                    dk = math.hypot(x - kx, (y - ky) * 0.8)
                    if dk < kr * 1.8:
                        w = 1 - dk / (kr * 1.8)
                        sp = math.sin(dk * 1.25 - math.atan2(y - ky, x - kx) * 2)
                        ridge = ridge * (1 - w) + sp * w
                        if dk < kr * 0.35: ridge = -1.6
                light = 0.08 + 0.34 * ((u + 1) / 2) ** 1.5          # moon is to the right of the trunk
                v = light + max(0, ridge) * 0.24 * (0.4 + (u + 1) / 2) - max(0, -ridge) * 0.1 + (fbm(x, y, 5, 6) - 0.5) * 0.12
                if abs(u) > 0.9: v -= 0.15
                if u > 0.8 and ridge > 0.3: v += 0.3                # moonlit rim
                px[x, y] = ramp(BARK, v, x, y)

        # ---------------- limbs: twisting up and out of frame, same coiling grain
        def limb(pts, seed):
            """pts: control points (x, y, radius). Catmull-Rom through them; shaded by the moon (lower right)."""
            P = [pts[0]] + pts + [pts[-1]]
            samples = []
            for i in range(1, len(P) - 2):
                p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
                for k in range(24):
                    t = k / 24
                    samples.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t * t
                                                + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t ** 3) for j in range(3)))
            samples.append(pts[-1])
            along = 0
            for i, (sx, sy, r) in enumerate(samples):
                if i: along += math.hypot(sx - samples[i - 1][0], sy - samples[i - 1][1])
                nx_, ny_ = (samples[min(i + 1, len(samples) - 1)][1] - samples[max(i - 1, 0)][1],
                            -(samples[min(i + 1, len(samples) - 1)][0] - samples[max(i - 1, 0)][0]))
                nl = math.hypot(nx_, ny_) or 1; nx_, ny_ = nx_ / nl, ny_ / nl
                if ny_ < 0: nx_, ny_ = -nx_, -ny_                    # normal pointing down (toward the moon)
                for yy in range(int(sy - r) - 1, int(sy + r) + 2):
                    for xx in range(int(sx - r) - 1, int(sx + r) + 2):
                        if not (0 <= xx < RW and 0 <= yy < RH): continue
                        ox, oy = xx - sx, yy - sy
                        if ox * ox + oy * oy > r * r: continue
                        perp = max(-1.0, min(1.0, (ox * nx_ + oy * ny_) / max(r, 1)))
                        ridge = math.sin(along * 0.5 + math.asin(perp) * 5 + fbm(xx, yy, seed, 7) * 2)
                        v = 0.1 + 0.32 * max(0, perp) + max(0, ridge) * 0.16 - max(0, -ridge) * 0.06
                        if perp > 0.82: v += 0.22
                        px[xx, yy] = ramp(BARK, v, xx, yy)
        limb([(90, 78, 14), (112, 50, 12), (140, 30, 10), (170, 16, 8), (200, 4, 7), (226, -8, 6)], 61)
        limb([(70, 64, 13), (56, 38, 11), (44, 16, 9), (36, -8, 8)], 62)
        limb([(128, 38, 6), (128, 24, 4.5), (122, 8, 3.5), (118, -6, 3)], 63)    # offshoot climbing out of frame

        # ---------------- canopy: leaf clumps hanging off the top edge (moonlit undersides)
        clumps = [(int(-10 + hsh(i, 31) * 230), int(hsh(i, 32) * 18) - 8, 10 + int(hsh(i, 33) * 14)) for i in range(26)]
        clumps += [(-6, 26, 20), (24, 12, 18), (200, -4, 16), (236, -8, 14), (120, -4, 9)]
        for cx, cy, r in clumps:
            for y in range(max(0, cy - r), min(RH, cy + r + 1)):
                for x in range(max(0, cx - r - 4), min(RW, cx + r + 5)):
                    dd = math.hypot((x - cx) * 0.8, y - cy) / r
                    edge = fbm(x, y, 11, 4) * 0.45
                    if dd > 0.75 + edge: continue
                    v = 0.25 + 0.35 * ((y - cy) / r) + 0.15 * ((x - cx) / r) + (fbm(x, y, 12, 3) - 0.5) * 0.6
                    if dd > 0.7 + edge * 0.8: v -= 0.25
                    px[x, y] = ramp(LEAF, v, x, y)

    # ---------------- the castle, close up: same stone as the keep behind, rising past the top
    WALL_X = 250
    for y in range(0, FLOOR):
        for x in range(WALL_X, RW):
            px[x, y] = stone(x, y, 0.32)
    for y in range(0, FLOOR):                                   # moonlit corner edge, buttress
        px[WALL_X, y] = IN['cs0']; px[WALL_X + 1, y] = IN['cs3'] if y % 2 else IN['cs2']
        for x in range(WALL_X + 30, WALL_X + 36):
            px[x, y] = stone(x, y, 0.5) if x < WALL_X + 32 else (IN['cs0'] if x > WALL_X + 34 else stone(x, y, 0.2))
    # tall lancet windows, warm and glowing like the title screen
    def window(wx, wy, w, h):
        for y in range(wy - 3, wy + h + 4):
            for x in range(wx - 4, wx + w + 4):
                if 0 <= x < RW and 0 <= y < RH and (x + y) % 2 == 0 and px[x, y] in (IN['cs1'], IN['cs2']):
                    px[x, y] = IN['cs3']                         # glow spill
        for y in range(wy, wy + h):
            for x in range(wx, wx + w):
                top = wy + (abs(x - (wx + (w - 1) / 2)) > (y - wy) * 0.9)
                if y < wy + w // 2 and abs(x - (wx + (w - 1) / 2)) > (y - wy) + 0.5: continue
                c = IN['win1'] if y < wy + h * 0.6 else IN['win0']
                if x == wx and y > wy + 2: c = IN['win2']
                px[x, y] = c
        px[wx + w // 2, wy + 3] = IN['win3']
        for x in range(wx - 1, wx + w + 1): px[x, wy + h] = IN['cs3']   # sill
    window(300, 22, 6, 18); window(326, 22, 6, 18); window(268, 70, 5, 14); window(334, 84, 6, 16)
    # gatehouse: open arch with a warm passage (exit back inside)
    GX0, GX1, GTOP = 306, 354, 120
    cxg, rr = (GX0 + GX1) / 2, (GX1 - GX0) / 2
    for y in range(GTOP - 8, FLOOR):
        for x in range(GX0 - 8, GX1 + 8):
            inner = y >= GTOP + rr - math.sqrt(max(0, rr * rr - (x + .5 - cxg) ** 2)) and GX0 <= x < GX1
            outer = y >= GTOP - 6 + rr + 6 - math.sqrt(max(0, (rr + 6) ** 2 - (x + .5 - cxg) ** 2)) and GX0 - 6 <= x < GX1 + 6
            if inner:
                t = (y - GTOP) / (FLOOR - GTOP)
                px[x, y] = ramp(['cs0', 'cs1', 'win0', 'win1', 'win2'], t ** 2.4 * 0.95, x, y)
            elif outer:
                v = 0.6 if x > cxg else 0.35                    # voussoir stones, moonlit left face
                if (math.atan2(y - (GTOP + rr), x + .5 - cxg) * 7) % 1 < 0.15: v = 0.05
                px[x, y] = ramp(['cs0', 'cs1', 'cs2', 'cs3'], v, x, y)
    for x in range(GX0 + 4, GX1 - 2, 6):                        # raised portcullis
        for y in range(GTOP + 6, GTOP + 18): px[x, y] = IN['cs0']
        px[x, GTOP + 18] = IN['bk6']
    for y in range(GTOP + 10, GTOP + 12):
        for x in range(GX0 + 3, GX1 - 2): px[x, y] = IN['cs0']
    # wall torches either side of the gate, with glow
    for tx in (292, 358):
        for y in range(150, 168):
            for x in range(tx - 9, tx + 10):
                if 0 <= x < RW and math.hypot(x - tx, (y - 154) * 1.2) < 9 and (x + y) % 2 == 0: px[x, y] = IN['cs3']
        for y in range(152, 160): px[min(RW - 1, tx), y] = IN['bk2']
        px[min(RW - 1, tx), 151] = IN['win1']; px[min(RW - 1, tx), 150] = IN['win2']; px[min(RW - 1, tx), 149] = IN['win3']

    # ---------------- ground: dark grass, a stone path to the gate, root shadows
    for y in range(FLOOR, RH):
        for x in range(RW):
            depth = (y - FLOOR) / (RH - FLOOR)
            v = 0.62 - depth * 0.55 + (fbm(x, y, 41, 5) - 0.5) * 0.35
            px[x, y] = ramp(GROUND, v, x, y)
            # path: flagstones widening toward the viewer (perspective), leading to the gate
            pc = 330 - (y - FLOOR) * 2.4; pw = 22 + (y - FLOOR) * 2.2
            if abs(x - pc) < pw:
                gx, gy = (x + (y // 4) * 5) // 9, y // 4
                c = IN['bk2'] if hsh(gx, gy, 6) > 0.4 else IN['bk3']
                if (x + (y // 4) * 5) % 9 == 0 or y % 4 == 0: c = IN['gr1']
                px[x, y] = c
    for x in range(RW):                                         # grass lip catching moonlight
        if px[x, FLOOR][:3] != IN['bk2'][:3]:
            px[x, FLOOR] = IN['gr4'] if hsh(x, 7) > 0.35 else IN['gr3']
            if hsh(x, 8) > 0.72: px[x, FLOOR - 1] = IN['gr4']
            if hsh(x, 9) > 0.9: px[x, FLOOR - 2] = IN['gr3']
    if after: after(im, px)                                     # e.g. surface roots lying on the grass
    return im

# =============================================================== scaled drawing
class SD:
    """ImageDraw that works in base-sprite coordinates scaled by k, so a sprite can be redrawn
    bigger with real detail (not upscaled pixels). k = 1 behaves like ImageDraw."""
    def __init__(self, im, k): self.d = ImageDraw.Draw(im); self.k = k
    def _pt(self, x, y): return (x, y) if self.k == 1 else ((x + 0.5) * self.k - 0.5, (y + 0.5) * self.k - 0.5)
    def _box(self, b):
        if self.k == 1: return b                                  # identical to plain ImageDraw
        x0, y0, x1, y1 = b; k = self.k
        x0, x1 = min(x0, x1), max(x0, x1); y0, y1 = min(y0, y1), max(y0, y1)
        return (round(x0 * k), round(y0 * k), round((x1 + 1) * k) - 1, round((y1 + 1) * k) - 1)
    def ellipse(self, b, fill): self.d.ellipse(self._box(b), fill=fill)
    def rectangle(self, b, fill): self.d.rectangle(self._box(b), fill=fill)
    def polygon(self, pts, fill): self.d.polygon([self._pt(x, y) for x, y in pts], fill=fill)
    def line(self, xy, fill, width=1):
        pts = [self._pt(xy[i], xy[i + 1]) for i in range(0, len(xy), 2)]
        self.d.line(pts, fill=fill, width=max(1, round(width * self.k)))
    def px(self, xy, c):
        if self.k == 1:
            w, h = self.d.im.size
            if 0 <= xy[0] < w and 0 <= xy[1] < h: self.d.point(xy, fill=c)
        else: self.rectangle((xy[0], xy[1], xy[0], xy[1]), c)

# Boss palettes: the Dread Wyrm is obsidian (the castle's purple-black) with a magma belly;
# the Ogre Warlord is a darker, scarred ogre in iron.
WYRM = dict(C, r0=hx('#0F0E19'), r1=hx('#1A1934'), r2=hx('#2A2F76'), r3=hx('#3D3680'),
            g2=hx('#E89A3C'), g1=hx('#B8641E'), fl2=hx('#FFF3C4'), bone=hx('#C9C6D8'), bone2=hx('#8A86A8'))
WARLORD = dict(C, o0=hx('#141E10'), o1=hx('#26381C'), o2=hx('#3C5626'), o3=hx('#55753A'),
               w1=hx('#1C2030'), w2=hx('#3A4058'), w3=hx('#6A7290'), eye=hx('#FF3A2A'))
BOSS_K = {'wyrm': 2.4, 'warlord': 2.0}

def wyrm(pose):
    im = dragon(pose, k=BOSS_K['wyrm'], pal=WYRM)
    px = im.load(); w, h = im.size
    src = im.copy(); sp = src.load()
    body = {WYRM['r1'], WYRM['r2'], WYRM['r0']}
    belly = {WYRM['g2'], WYRM['g1']}
    for y in range(h):
        for x in range(w):
            c = sp[x, y]
            if not c[3]: continue
            up = sp[x, y - 1] if y else (0, 0, 0, 0)
            if c in body and up == C['K']:                      # moonlit rim along every top edge
                px[x, y] = WYRM['r3']
            elif c in body and (x + 2 * (y // 3)) % 5 == 0 and y % 3 == 0:
                px[x, y] = WYRM['r2'] if c != WYRM['r2'] else WYRM['r3']   # scales
            elif c in belly:                                     # cooled crust over glowing magma cracks
                crack = math.sin(x * 0.55 + math.sin(y * 0.8) * 2) > 0.75 or math.sin(y * 0.9 + x * 0.2) > 0.9
                px[x, y] = hx('#FFC872') if crack else (hx('#3A1A12') if (x + y) % 2 else hx('#5A2614'))
    return im
def warlord(pose): return ogre(pose, k=BOSS_K['warlord'], pal=WARLORD, armor=True)

# =============================================================== ogre
OW, OH, OCX = 48, 48, 22
def ogre(pose, k=1, pal=None, armor=False):
    pal = pal or C
    """pose: walk1 | walk2 | windup | smash. Faces right."""
    im = Image.new('RGBA', (round(OW * k), round(OH * k)), (0, 0, 0, 0)); d = SD(im, k)
    bob = 1 if pose == 'walk2' else 0
    lean = {'windup': -2, 'smash': 3}.get(pose, 0)
    fb = 47                                                   # feet bottom row
    # legs
    legs = {'walk1': ((OCX - 6, OCX - 9), (OCX + 3, OCX + 6)), 'walk2': ((OCX - 4, OCX - 4), (OCX + 1, OCX + 1)),
            'windup': ((OCX - 6, OCX - 8), (OCX + 3, OCX + 5)), 'smash': ((OCX - 7, OCX - 10), (OCX + 4, OCX + 8))}[pose]
    for (hipx, footx), col in zip(legs, ('o1', 'o2')):
        d.line((hipx + 2, 36 + bob, footx + 2, fb - 2), fill=pal[col], width=6)
        d.rectangle((footx - 1, fb - 2, footx + 6, fb), fill=pal['o0'])
    # back arm
    d.line((OCX - 4 + lean, 22 + bob, OCX - 8 + lean, 34 + bob), fill=pal['o1'], width=5)
    # body: hunched torso + big belly
    d.ellipse((OCX - 12 + lean, 14 + bob, OCX + 8 + lean, 34 + bob), fill=pal['o1'])       # back/shoulders
    d.ellipse((OCX - 8 + lean, 20 + bob, OCX + 12 + lean, 40 + bob), fill=pal['o2'])       # belly
    d.ellipse((OCX - 1 + lean, 25 + bob, OCX + 9 + lean, 36 + bob), fill=pal['o3'])        # belly highlight
    if armor:                                                    # spiked pauldron + chest strap
        d.ellipse((OCX - 11 + lean, 13 + bob, OCX + 1 + lean, 22 + bob), fill=pal['iron1'])
        d.ellipse((OCX - 10 + lean, 13 + bob, OCX + lean, 17 + bob), fill=pal['iron2'])
        for sx in (-9, -5, -1): d.polygon([(OCX + sx + lean, 14 + bob), (OCX + sx + 1 + lean, 9 + bob), (OCX + sx + 2 + lean, 14 + bob)], fill=pal['bone'])
        d.line((OCX - 8 + lean, 18 + bob, OCX + 9 + lean, 36 + bob), fill=pal['iron1'], width=2)
    d.rectangle((OCX - 9, 36 + bob, OCX + 11, 39 + bob), fill=pal['w1'])                     # loincloth
    d.rectangle((OCX - 9, 36 + bob, OCX + 11, 36 + bob), fill=pal['w3'])
    d.polygon([(OCX - 2, 39 + bob), (OCX + 6, 39 + bob), (OCX + 4, 44 + bob), (OCX, 44 + bob)], fill=pal['w1'])
    # head: small, forward, underbite with tusks
    hx0, hy0 = OCX + 4 + lean, 9 + bob + (2 if pose == 'smash' else 0)
    def draw_head():
      d.ellipse((hx0, hy0, hx0 + 11, hy0 + 11), fill=pal['o2'])
      d.rectangle((hx0 + 6, hy0 + 7, hx0 + 12, hy0 + 11), fill=pal['o2'])                     # jaw
      d.rectangle((hx0 + 2, hy0 + 2, hx0 + 9, hy0 + 3), fill=pal['o1'])                      # brow
      d.px((hx0 + 8, hy0 + 4), pal['eye'])
      d.px((hx0 + 10, hy0 + 6), pal['bone']); d.px((hx0 + 10, hy0 + 7), pal['bone'])   # tusks
      d.px((hx0 + 12, hy0 + 6), pal['bone'])
      d.ellipse((hx0 - 1, hy0 + 3, hx0 + 2, hy0 + 7), fill=pal['o1'])                          # ear
      if armor:                                                  # horned iron war-helm
        d.ellipse((hx0 - 1, hy0 - 2, hx0 + 12, hy0 + 6), fill=pal['iron1'])
        d.rectangle((hx0 - 1, hy0 + 2, hx0 + 12, hy0 + 3), fill=pal['iron2'])
        d.px((hx0 + 8, hy0 + 4), pal['eye'])
        d.line((hx0 + 1, hy0, hx0 - 3, hy0 - 4), fill=pal['bone'], width=2)
        d.line((hx0 - 3, hy0 - 4, hx0 - 3, hy0 - 8), fill=pal['bone'], width=1)
        d.line((hx0 + 10, hy0 - 1, hx0 + 13, hy0 - 5), fill=pal['bone'], width=2)
        d.line((hx0 + 13, hy0 - 5, hx0 + 13, hy0 - 9), fill=pal['bone'], width=1)
    draw_head()
    # front arm + club
    sh = (OCX + 2 + lean, 21 + bob)
    hand, club_end = {
        'walk1': ((OCX + 10, 33), (OCX + 20, 22)), 'walk2': ((OCX + 10, 34), (OCX + 20, 24)),
        'windup': ((OCX - 7, 14), (OCX - 18, 1)), 'smash': ((OCX + 16, 36), (OCX + 25, 46)),
    }[pose]
    hand = (hand[0], hand[1] + bob); club_end = (club_end[0], club_end[1] + bob)
    def draw_arm_club():
        d.line((*sh, *hand), fill=pal['o2'], width=5)
        d.ellipse((hand[0] - 3, hand[1] - 3, hand[0] + 3, hand[1] + 3), fill=pal['o3'])
        club()
    def club():
        n = 10
        for k in range(n + 1):
            t = k / n; x = hand[0] + (club_end[0] - hand[0]) * t; y = hand[1] + (club_end[1] - hand[1]) * t
            r = 1 + t * 3.2
            d.ellipse((x - r, y - r, x + r, y + r), fill=pal['w2'] if t < 0.95 else pal['w1'])
        ex, ey = club_end
        for sx, sy in ((-2, -1), (1, 2), (2, -2)):
            d.px((max(0, min(OW - 1, ex + sx)), max(0, min(OH - 1, ey + sy))), pal['iron2'])
    if pose == 'windup':                      # club raised behind the head: redraw head on top
        draw_arm_club(); draw_head()
    else:
        draw_arm_club()
    im = outline(im)
    return im

# =============================================================== dragon
DW, DH = 64, 48
def dragon(pose, k=1, pal=None):
    pal = pal or C
    """pose: fly1 (wings up) | fly2 (level) | fly3 (down) | breathe. Faces right."""
    im = Image.new('RGBA', (round(DW * k), round(DH * k)), (0, 0, 0, 0)); d = SD(im, k)
    bob = {'fly1': 1, 'fly2': 0, 'fly3': -1, 'breathe': 0}[pose]
    by = 26 + bob
    wing_state = {'fly1': 'up', 'fly2': 'mid', 'fly3': 'down', 'breathe': 'mid'}[pose]
    def wing(near):
        base = (28, by - 4) if near else (32, by - 5)
        tips = {'up':   [(16, 2), (26, 0), (38, 4)],
                'mid':  [(6, by - 12), (18, by - 16), (34, by - 14)],
                'down': [(8, by + 14), (18, by + 18), (30, by + 14)]}[wing_state]
        if not near: tips = [(x + 6, y - 2) for x, y in tips]
        poly = [base, tips[0], (tips[0][0] + 4, tips[0][1] + (6 if wing_state != 'down' else -6)),
                tips[1], (tips[1][0] + 5, tips[1][1] + (6 if wing_state != 'down' else -6)), tips[2], (base[0] + 10, base[1])]
        d.polygon(poly, fill=pal['r1' if near else 'r0'])
        for t in tips: d.line((*base, *t), fill=pal['r3' if near else 'r1'], width=1)   # wing bones
    wing(False)
    # tail: tapering curve to a spade
    pts = [(24 - k * 2.2, by + 2 + math.sin(k * 0.5) * 3) for k in range(10)]
    for k, (x, y) in enumerate(pts):
        r = 3.2 - k * 0.28
        d.ellipse((x - r, y - r, x + r, y + r), fill=pal['r1'])
    tx, ty = pts[-1]
    d.polygon([(tx - 1, ty), (tx - 5, ty - 3), (tx - 6, ty + 1), (tx - 4, ty + 4)], fill=pal['r2'])
    # body
    d.ellipse((20, by - 6, 44, by + 7), fill=pal['r1'])
    d.ellipse((22, by - 6, 42, by + 1), fill=pal['r2'])
    d.ellipse((24, by + 1, 42, by + 7), fill=pal['g2'])                         # belly scales
    for x in range(26, 42, 3): d.px((x, by + 4), pal['g1'])
    # legs tucked
    d.line((28, by + 6, 26, by + 10), fill=pal['r1'], width=2); d.line((37, by + 6, 36, by + 10), fill=pal['r1'], width=2)
    for x in (24, 26, 34, 36): d.px((x, by + 11), pal['bone'])
    # neck + head
    d.line((40, by - 2, 47, by - 8), fill=pal['r1'], width=5)
    d.line((40, by + 1, 47, by - 5), fill=pal['g2'], width=2)
    hx0, hy0 = 45, by - 13
    d.polygon([(hx0, hy0 + 2), (hx0 + 6, hy0), (hx0 + 14, hy0 + 4), (hx0 + 14, hy0 + 7), (hx0 + 6, hy0 + 8), (hx0, hy0 + 7)], fill=pal['r2'])
    if pose == 'breathe':
        d.polygon([(hx0 + 4, hy0 + 8), (hx0 + 14, hy0 + 11), (hx0 + 6, hy0 + 11)], fill=pal['r1'])   # open jaw
        d.ellipse((hx0 + 12, hy0 + 5, hx0 + 18, hy0 + 11), fill=pal['fl1'])
        d.ellipse((hx0 + 13, hy0 + 6, hx0 + 16, hy0 + 9), fill=pal['fl2'])
        d.px((hx0 + 14, hy0 + 7), pal['fl3'])
    else:
        d.line((hx0 + 6, hy0 + 7, hx0 + 13, hy0 + 6), fill=pal['r1'])          # mouth line
    d.px((hx0 + 8, hy0 + 3), pal['fl2'])                                # eye
    d.line((hx0 + 2, hy0 + 1, hx0 - 3, hy0 - 4), fill=pal['bone'], width=1)     # horns
    d.line((hx0 + 4, hy0, hx0 + 1, hy0 - 5), fill=pal['bone2'], width=1)
    # spines along the back
    for x in range(22, 42, 4): d.px((x, by - 7), pal['r3'])
    wing(True)
    fire = (pal['fl0'], pal['fl1'], pal['fl2'], pal['fl3'])
    return outline(im, skip=fire)

def fireball(f):
    im = Image.new('RGBA', (14, 14), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    j = 1 if f else 0
    d.ellipse((1, 3 - j, 11, 13 - j), fill=C['fl0'])
    d.ellipse((3, 5 - j, 10, 12 - j), fill=C['fl1'])
    d.ellipse((5, 7 - j, 9, 11 - j), fill=C['fl2'])
    im.putpixel((7, 9 - j), C['fl3'])
    d.polygon([(3, 4 - j), (5, 0 + j), (6, 4)], fill=C['fl1'])                # flicker tongue
    return im

def heart(full):
    rows = ['.##.##.', '#######', '#######', '.#####.', '..###..', '...#...']
    im = Image.new('RGBA', (9, 8), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            if c == '#': im.putpixel((x + 1, y + 1), C['heart'] if full else C['heartd'])
    if full: im.putpixel((2, 2), C['heart2']); im.putpixel((3, 2), C['heart2'])
    return outline(im)

# =============================================================== output
def frames():
    return {
        'ogre': {p: ogre(p) for p in ('walk1', 'walk2', 'windup', 'smash')},
        'dragon': {p: dragon(p) for p in ('fly1', 'fly2', 'fly3', 'breathe')},
        'fireball': {str(i + 1): fireball(i) for i in range(2)},
        'heart': {'full': heart(True), 'empty': heart(False)},
    }

def write():
    sp = os.path.join(ROOT, 'public/assets/sprites')
    courtyard().convert('RGB').save(os.path.join(ROOT, 'public/assets/rooms/courtyard.png'))
    for kind, fr in frames().items():
        for name, im in fr.items():
            im.save(os.path.join(sp, f'{kind}_{name}_right.png') if kind in ('ogre', 'dragon') else os.path.join(sp, f'{kind}_{name}.png'))
            if kind in ('ogre', 'dragon'): mirror(im).save(os.path.join(sp, f'{kind}_{name}_left.png'))
    print('wrote courtyard + sprites')

def preview():
    dest = os.path.join(ROOT, 'arena-options'); os.makedirs(dest, exist_ok=True)
    S = 4
    font = ImageFont.load_default(size=26); small = ImageFont.load_default(size=18)
    fr = frames()
    # 1) sprite sheet at 6x
    sc = 6; pad = 12
    items = [(f'ogre {k}', v) for k, v in fr['ogre'].items()] + [(f'dragon {k}', v) for k, v in fr['dragon'].items()] + \
            [('fireball', fr['fireball']['1']), ('heart', fr['heart']['full'])]
    wsum = sum(im.width * sc + pad for _, im in items) + pad
    sheet = Image.new('RGBA', (wsum, DH * sc + 70), (16, 20, 44, 255)); dd = ImageDraw.Draw(sheet); x = pad
    for label, im in items:
        sheet.alpha_composite(im.resize((im.width * sc, im.height * sc), Image.NEAREST), (x, 44 + (DH - im.height) * sc))
        dd.text((x, 10), label, font=small, fill=(232, 164, 90, 255)); x += im.width * sc + pad
    sheet.convert('RGB').save(os.path.join(dest, 'enemies.png'))
    # 2) full mock-up of the mini-game screen at 4x
    for opt in ('A', 'C'):
      bg = courtyard(opt)
      knight = Image.open(os.path.join(ROOT, 'public/assets/sprites/hk_slash_right_2.png'))
      scene = bg.copy()
      def put(im, x, y): scene.alpha_composite(im, (int(x), int(y)))
      put(mirror(fr['ogre']['walk1']), 196, FLOOR - OH)            # ogre approaching from the right
      put(fr['ogre']['windup'], 70, FLOOR - OH)                     # ogre winding up on the left
      put(knight, 150 - 22, FLOOR - 60)
      put(mirror(fr['dragon']['breathe']), 196, 40)
      put(fr['fireball']['1'], 160, 92); put(fr['fireball']['2'], 182, 70)
      big = scene.resize((RW * S, RH * S), Image.NEAREST)
      hud = ImageDraw.Draw(big)
      pf = ImageFont.load_default(size=22)
      # hearts top-left
      hb = Image.new('RGBA', (1, 1))
      for i in range(5):
          h = fr['heart']['full' if i < 4 else 'empty']
          big.alpha_composite(h.resize((h.width * S, h.height * S), Image.NEAREST), (28 + i * 40, 28))
      def box(x0, y0, x1, y1): hud.rectangle((x0, y0, x1, y1), fill=(5, 7, 15, 190), outline=(58, 74, 117, 255), width=3)
      box(560, 18, 880, 110); hud.text((720, 30), 'WAVE 3', font=font, anchor='mt', fill=(242, 230, 207, 255))
      hud.text((720, 70), 'SCORE 01450   x3 COMBO', font=pf, anchor='mt', fill=(232, 164, 90, 255))
      box(1180, 18, 1416, 110); hud.text((1298, 34), 'HIGH SCORE', font=small, anchor='mt', fill=(138, 148, 168, 255))
      hud.text((1298, 66), 'SAI  04200', font=pf, anchor='mt', fill=(143, 191, 138, 255))
      box(470, 840, 970, 884); hud.text((720, 852), '<- ->  MOVE   SPACE JUMP   X SLASH   ESC QUIT', font=small, anchor='mt', fill=(169, 180, 214, 255))
      big.convert('RGB').save(os.path.join(dest, f'mockup-{opt}.png'))
    print('wrote previews to', dest)


def boss_preview():
    """Two final-boss candidates: sprite sheets + in-scene mock-ups -> arena-options/."""
    dest = os.path.join(ROOT, 'arena-options'); os.makedirs(dest, exist_ok=True)
    S = 4
    big_f = ImageFont.load_default(size=24); small = ImageFont.load_default(size=18)
    knight_jump = Image.open(os.path.join(ROOT, 'public/assets/sprites/hk_walk_right_1.png'))
    knight_slash = Image.open(os.path.join(ROOT, 'public/assets/sprites/hk_slash_right_2.png'))
    fb = fireball(0); fb2 = fireball(1)
    def hud(big, name, frac):
        h = ImageDraw.Draw(big)
        for i in range(5):
            hh = heart(i < 3)
            big.alpha_composite(hh.resize((hh.width * S, hh.height * S), Image.NEAREST), (28 + i * 40, 28))
        h.rectangle((380, 20, 1060, 92), fill=(5, 7, 15, 200), outline=(58, 74, 117, 255), width=3)
        h.text((720, 30), name, font=big_f, anchor='mt', fill=(232, 164, 90, 255))
        h.rectangle((400, 64, 1040, 80), fill=(22, 29, 51, 255), outline=(4, 6, 15, 255), width=3)
        h.rectangle((403, 67, 403 + int(634 * frac), 77), fill=(208, 74, 94, 255))
        h.rectangle((470, 840, 970, 884), fill=(5, 7, 15, 190), outline=(58, 74, 117, 255), width=3)
        h.text((720, 852), 'FINAL BATTLE  ·  WAVE 5 CLEARED', font=small, anchor='mt', fill=(169, 180, 214, 255))
    # A: the Dread Wyrm raining fire
    scene = courtyard()
    w = wyrm('breathe'); w = mirror(w)
    scene.alpha_composite(w, (150, 6))
    for x, y, f in ((120, 70, fb), (88, 110, fb2), (150, 128, fb), (200, 96, fb2), (60, 150, fb), (236, 150, fb2)):
        scene.alpha_composite(f, (x, y))
    scene.alpha_composite(knight_jump, (100 - 22, FLOOR - 60 - 18))
    big = scene.resize((RW * S, RH * S), Image.NEAREST); hud(big, 'THE DREAD WYRM', 0.82)
    big.convert('RGB').save(os.path.join(dest, 'boss-A-wyrm.png'))
    # B: the Ogre Warlord about to slam
    scene = courtyard()
    wl = mirror(warlord('windup'))
    scene.alpha_composite(wl, (200, FLOOR - wl.height))
    d = ImageDraw.Draw(scene)
    for i, x in enumerate(range(60, 200, 6)):                    # shockwave rolling along the ground
        hgt = 2 + (i % 3)
        d.rectangle((x, FLOOR - hgt, x + 3, FLOOR - 1), fill=C['fl1'] if i % 2 else C['fl2'])
    scene.alpha_composite(knight_slash, (120 - 22, FLOOR - 60))
    big = scene.resize((RW * S, RH * S), Image.NEAREST); hud(big, 'THE OGRE WARLORD', 0.9)
    big.convert('RGB').save(os.path.join(dest, 'boss-B-warlord.png'))
    # sheets at 4x on a dark ground, with the knight for scale
    for key, fn_, poses in (('A-wyrm', wyrm, ['fly1', 'fly2', 'fly3', 'breathe']), ('B-warlord', warlord, ['walk1', 'windup', 'smash'])):
        frames = [fn_(p) for p in poses]
        kn = Image.open(os.path.join(ROOT, 'public/assets/sprites/hk_idle_right.png'))
        items = frames + [kn]
        hmax = max(i.height for i in items)
        sheet = Image.new('RGBA', (sum(i.width * S + 24 for i in items) + 24, hmax * S + 70), (16, 20, 44, 255))
        x = 24
        for i, im in enumerate(items):
            sheet.alpha_composite(im.resize((im.width * S, im.height * S), Image.NEAREST), (x, 50 + (hmax - im.height) * S))
            ImageDraw.Draw(sheet).text((x, 14), (poses + ['knight (scale)'])[i], font=small, fill=(232, 164, 90, 255))
            x += im.width * S + 24
        sheet.convert('RGB').save(os.path.join(dest, f'boss-{key}-sheet.png'))
    print('wrote boss previews to', dest)

if __name__ == '__main__':
    arg = sys.argv[1] if len(sys.argv) > 1 else 'preview'
    {'preview': preview, 'write': write, 'boss': boss_preview}.get(arg, lambda: sys.exit('use preview or write'))()
