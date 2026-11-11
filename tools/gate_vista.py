"""The view out through the Gate Hall's arch: a moonlit vista that matches the courtyard outside.
Usage: python3 tools/gate_vista.py preview | write <name>
Used by tools/sign_runes.py (base()) so the gate room is always rebuilt with it."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
import arena_art as A
from tree_art import ramp, hx, pal, PALETTES, SKYC

fbm, noise, hsh, BAYER = A.fbm, A.noise, A.hsh, A.BAYER
X0, X1, Y0, Y1 = 136, 224, 56, 196           # search box around the arch opening

def opening_mask(im):
    """flood fill the outside view from the middle of the arch (sky + landscape colours only)"""
    px = im.load()
    inside = set()
    for y in range(100, Y1):
        for x in range(139, 221): inside.add(px[x, y][:3])
    inside |= {(11, 19, 48), (217, 210, 195), (230, 240, 255), (140, 180, 232)}
    inside -= {(76, 88, 136), (52, 62, 102), (29, 37, 74), (22, 28, 58), (8, 10, 24), (17, 22, 44)}   # the arch's stones
    seen, stack = set(), [(180, 150)]
    while stack:
        x, y = stack.pop()
        if (x, y) in seen or not (X0 <= x < X1 and Y0 <= y < Y1) or px[x, y][:3] not in inside: continue
        seen.add((x, y))
        stack += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    return seen

MOSS = PALETTES['mossy']
MOON = (198, 104)
HZ = hx('#2A2F76')

def haze(c, k):
    return tuple(int(c[j] * (1 - k) + HZ[j] * k) for j in range(3)) + (255,)

def vista(name):
    """returns {(x, y): colour} in room coordinates for every pixel of the view"""
    out = {}
    tree = name in ('forest', 'lake')
    lake = name == 'lake'
    town = name == 'town'
    HOR = 168                                   # horizon line
    for y in range(Y0, Y1):
        for x in range(X0, X1):
            # sky: deep at the top, violet glow at the horizon and round the moon
            dm = math.hypot(x - MOON[0], y - MOON[1])
            v = 0.12 + ((y - Y0) / (HOR - Y0)) ** 1.6 * 0.5 + max(0, 0.3 - dm / 70)
            c = ramp(SKYC, v, x, y)
            if hsh(x, y, 5) > 0.992 and dm > 10 and y < HOR - 20: c = hx('#E6F0FF') if hsh(x, y, 6) > 0.4 else SKYC[6]
            out[(x, y)] = c
    # moon with a dithered halo
    for y in range(MOON[1] - 14, MOON[1] + 15):
        for x in range(MOON[0] - 14, MOON[0] + 15):
            d = math.hypot(x - MOON[0], y - MOON[1])
            if d <= 6.5: out[(x, y)] = hx('#F6F3E8') if d < 5.6 else hx('#C9C6D8')
            elif d < 9 and (x + y) % 2 == 0: out[(x, y)] = SKYC[5]
            elif d < 13 and (x + y) % 4 == 0: out[(x, y)] = SKYC[4]
    out[(MOON[0] - 2, MOON[1] - 1)] = hx('#C9C6D8'); out[(MOON[0] + 2, MOON[1] + 2)] = hx('#C9C6D8')
    # far mountains (hazy, lit edge facing the moon)
    for x in range(X0, X1):
        h = HOR - 18 + 7 * math.sin(x * 0.09 + 1) + 5 * math.sin(x * 0.23) + 4 * fbm(x, 0, 21, 5) * 2
        for y in range(int(h), HOR + 2):
            c = ramp(SKYC, 0.42 - (y - h) / 50, x, y)
            if y == int(h): c = SKYC[6]
            out[(x, y)] = c
        if town and 150 < x < 210 and hsh(x, 3, 31) > 0.8:               # distant village lights
            out[(x, int(h) + 4 + int(hsh(x, 4, 32) * 6))] = hx('#FFC872')
    # pine forest band
    for i in range(40):
        tx = X0 + int(i * 2.4 + hsh(i, 41) * 3); th = 6 + int(hsh(i, 42) * 9)
        for k in range(th):
            half = int(k / th * 2.6)
            for xx in range(tx - half, tx + half + 1):
                out[(xx, HOR + 4 - th + k)] = SKYC[1] if hsh(xx, k, 43) > 0.15 else SKYC[2]
    # ground: lake reflecting the moon, or a meadow with a path running out to the courtyard
    for y in range(HOR + 4, Y1):
        for x in range(X0, X1):
            depth = (y - HOR) / (Y1 - HOR)
            if lake and y < HOR + 14:
                c = ramp(SKYC, 0.22 + 0.1 * math.sin(x * 0.9 + y * 2), x, y)
                if abs(x - MOON[0]) < 3 - (y - HOR) * 0.1 and (y % 2 == 0): c = hx('#C9C6D8')   # moon path on the water
                out[(x, y)] = c; continue
            g = MOSS['moss']
            c = ramp(g, 0.25 + depth * 0.25 + (fbm(x, y, 61, 4) - 0.5) * 0.4, x, y)
            c = haze(c, 0.55 - depth * 0.35)
            pc = 180 + (y - Y1) * 0.25; pw = 3 + depth * 26                       # path narrowing toward the horizon
            if abs(x - pc) < pw:
                row = int(depth * 9)
                c = hx('#263D58') if hsh((x - int(pc)) // max(2, int(pw / 3)), row, 62) > 0.4 else hx('#1A2B4D')
                if (y % max(2, int(1 + depth * 4))) == 0: c = hx('#0E1C3A')
                c = haze(c, 0.35 - depth * 0.25)
            out[(x, y)] = c
    # the giant tree framing the left side (part of the courtyard outside)
    if tree:
        bark = MOSS['bark']
        for y in range(Y0, Y1):
            cx = X0 + 8 + 3 * math.sin(y * 0.05)
            hw = 14 + (max(0, y - 170) / 26) ** 2 * 12
            for x in range(X0, int(cx + hw) + 1):
                u = (x - cx) / hw
                if u > 1: continue
                ridge = math.sin(7 * (math.asin(max(-1, min(1, u))) + y * 0.05))
                v = 0.12 + 0.3 * max(0, u) + max(0, ridge) * 0.12
                if u > 0.82: v += 0.2
                out[(x, y)] = haze(ramp(bark, v, x, y), 0.25)
        # a limb arching over the top with hanging leaves
        for x in range(X0, X1):
            yy = Y0 + 14 + (x - X0) * 0.18 + 4 * math.sin(x * 0.07)
            r = max(1.5, 7 - (x - X0) * 0.06)
            for y in range(int(yy - r), int(yy + r) + 1):
                v = 0.15 + 0.25 * ((y - (yy - r)) / (2 * r))
                out[(x, y)] = haze(ramp(bark, v, x, y), 0.3)
        for i in range(16):
            lx = X0 + int(hsh(i, 71) * 56); ly = Y0 + int(10 + hsh(i, 72) * 18 + (lx - X0) * 0.18); r = 5 + int(hsh(i, 73) * 6)
            for y in range(ly - r, ly + r):
                for x in range(lx - r - 2, lx + r + 2):
                    d = math.hypot((x - lx) * 0.8, y - ly) / r
                    if d < 0.8 + fbm(x, y, 74, 3) * 0.4:
                        out[(x, y)] = haze(ramp(MOSS['leaf'], 0.2 + (y - ly) / r * 0.3 + (fbm(x, y, 75, 2) - 0.5) * 0.5, x, y), 0.3)
    # ground mist and fireflies
    for y in range(HOR - 6, Y1):
        for x in range(X0, X1):
            band = math.exp(-((y - (HOR + 8)) / 9.0) ** 2) * (0.4 + 0.9 * fbm(x * 0.4, y * 1.5, 81, 8))
            if band * 16 > BAYER[y % 4][x % 4] + 6 and (x, y) in out:
                out[(x, y)] = haze(out[(x, y)], 0.45)
    for i in range(9):
        out[(X0 + 8 + int(hsh(i, 91) * 70), HOR + 6 + int(hsh(i, 92) * 20))] = hx('#3FD0C8') if i % 2 else hx('#FFC872')
    return out

def apply(im, name):
    mask = opening_mask(im)
    v = vista(name); px = im.load()
    for p in mask:
        if p in v: px[p] = v[p]
    return im

VARIANTS = ['forest', 'lake', 'town']

if __name__ == '__main__':
    import sign_runes
    if sys.argv[1] == 'preview':
        tiles = [sign_runes.strip_bars(Image.open('tools/gate_base.png').convert('RGBA'))]
        for n in VARIANTS: tiles.append(apply(sign_runes.strip_bars(Image.open('tools/gate_base.png').convert('RGBA')), n))
        box = (120, 40, 240, 200); w, h = box[2] - box[0], box[3] - box[1]
        out = Image.new('RGBA', (4 * (w * 3 + 10), h * 3), (0, 0, 0, 255))
        for i, t in enumerate(tiles): out.paste(t.crop(box).resize((w * 3, h * 3), Image.NEAREST), (i * (w * 3 + 10), 0))
        out.save('sign-options/gate-vista.png')
