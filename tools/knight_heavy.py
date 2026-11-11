"""Side-view knight sprites styled after knight_seated_front.png, with adjustable build.

Usage:
  python3 tools/knight_heavy.py preview     # comparison images -> knight-options/ (game untouched)
  python3 tools/knight_heavy.py <VARIANT>   # write game sprites for one variant (e.g. B)

Game sprites written to public/assets/sprites/:
  hk_idle_{right,left}.png, hk_walk_{right,left}_{1..4}.png,
  hk_slash_{right,left}_{1..3}.png      all 60x60, feet on the bottom row
  hk_portrait.png                       helm crop for the HUD
  hk_sheet.png                          every frame at 6x

Every frame shares one canvas: body centre at x = CX (right-facing) or W - 1 - CX
(left-facing, mirrored), feet on row H - 1.
"""
import math, os, sys
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'public/assets/sprites')

PAL = {'K': '#0A0C16', 'H': '#E2E7EF', 'h': '#A4AEC2', 'd': '#5E687E', 'A': '#C2C9D8', 'a': '#727C96',
       'P': '#3E30A0', 'p': '#6352D0', 'q': '#241A62', 'V': '#0E1222', 'W': '#DCE3EE', 'w': '#8C96AC',
       'G': '#E0A640', 'g': '#8A6020', 'B': '#4A2E1C', 'T': '#8CB4E8', 't': '#4A6FA8'}
W, H = 60, 60
CX = 22          # body centre column (right-facing)
DY = 4           # layout is drawn with feet on row 55; shift down so feet sit on row 59
FOOT = 55

# Build settings. Heights: helm top = torso_top - 1 - helm_h, feet at 55.
VARIANTS = {
    'A': dict(name='Lean knight', helm_w=9, helm_h=9, helm_round=2, torso_top=24, belt_y=34, fauld_h=3,
              back=5, front=4, chest=1, waist=1, leg_t=3, knee_y=47, pauldron=(4.2, 2.6), arm_t=3,
              cape_back=6, cape_flare=8),
    'B': dict(name='Middle ground', helm_w=10, helm_h=10, helm_round=1, torso_top=23, belt_y=34, fauld_h=3,
              back=6, front=5, chest=1, waist=1, leg_t=4, knee_y=47, pauldron=(5.0, 3.0), arm_t=3,
              cape_back=7, cape_flare=9),
    'C': dict(name='Sturdy', helm_w=11, helm_h=11, helm_round=1, torso_top=22, belt_y=34, fauld_h=4,
              back=7, front=5, chest=1, waist=1, leg_t=4, knee_y=47, pauldron=(5.6, 3.4), arm_t=4,
              cape_back=8, cape_flare=10),
    # B redrawn at 80% size (~35 px tall instead of ~44). k scales poses, reach and blade length.
    'B80': dict(name='Middle ground, 80%', helm_w=8, helm_h=8, helm_round=1, torso_top=30, belt_y=39, fauld_h=2,
              back=5, front=4, chest=1, waist=1, leg_t=3, knee_y=49, pauldron=(4.0, 2.4), arm_t=3,
              cape_back=6, cape_flare=7, k=0.8),
    'X': dict(name='Current (too chunky)', helm_w=12, helm_h=12, helm_round=0, torso_top=21, belt_y=34, fauld_h=4,
              back=7, front=6, chest=1, waist=0, leg_t=5, knee_y=47, pauldron=(6.2, 3.8), arm_t=4,
              cape_back=8, cape_flare=10),
}
V = VARIANTS['B']

def blank(): return [['.'] * W for _ in range(H)]
def setp(g, x, y, c):
    x, y = int(round(x)), int(round(y + DY))
    if 0 <= y < H and 0 <= x < W: g[y][x] = c
def rect(g, x, y, w, h, c):
    for j in range(y, y + h):
        for i in range(x, x + w): setp(g, i, j, c)
def line(g, x0, y0, x1, y1, c, t=1):
    n = int(math.ceil(max(abs(x1 - x0), abs(y1 - y0), 1)))
    for k in range(n + 1):
        x = x0 + (x1 - x0) * k / n; y = y0 + (y1 - y0) * k / n
        for dx in range(t):
            for dy in range(t): setp(g, x + dx - t // 2, y + dy - t // 2, c)
def ell(g, cx, cy, rx, ry, fn):
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1: setp(g, x, y, fn(x, y))
def outline(g):
    out = [r[:] for r in g]
    for y in range(H):
        for x in range(W):
            if g[y][x] != '.': continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < W and 0 <= yy < H and g[yy][xx] not in '.KTt':
                    out[y][x] = 'K'; break
    return out

# ---------------------------------------------------------------- derived layout
def hip_y(): return V['belt_y'] + 1 + V['fauld_h']
def sk(v): return round(v * V.get('k', 1))      # scale a pose offset / length
def shoulder(oy): return (CX + 1, V['torso_top'] + sk(4) + oy)

# ---------------------------------------------------------------- parts
def cape(g, oy, sway):
    top, bot = V['torso_top'] - 1, FOOT - 2
    for y in range(top, bot + 1):
        t = (y - top) / (bot - top)
        xl = round(CX - V['cape_back'] - 1 - t * V['cape_flare'] - sway * t)
        xr = CX + 2
        for x in range(xl, xr):
            f = (x - xl) / max(1, xr - xl)
            c = 'q' if f < 0.18 else ('P' if f < 0.7 else 'p')
            if c == 'P' and (x - y // 4) % 6 == 0: c = 'q'      # folds
            setp(g, x, y + oy, c)
        if y == bot:                                           # ragged hem
            for x in range(xl, xr, 2): setp(g, x, y + 1 + oy, 'q')

def leg(g, hip, knee, foot, near):
    t = V['leg_t']
    c1, c2, c3 = ('a', 'h', 'd') if near else ('d', 'a', 'd')
    line(g, hip[0], hip[1], knee[0], knee[1], c1, t)
    line(g, knee[0], knee[1], foot[0], foot[1] - 2, c1, t)
    line(g, hip[0] + t // 2 - 1, hip[1], knee[0] + t // 2 - 1, knee[1], c2, 1)
    line(g, knee[0] + t // 2 - 1, knee[1], foot[0] + t // 2 - 1, foot[1] - 3, c2, 1)
    r = 1.4 + t * 0.3
    ell(g, knee[0] + 0.3, knee[1], r, r * 0.85, lambda x, y: c2 if y <= knee[1] else c3)   # knee cop
    fw = t + 2
    rect(g, foot[0] - t // 2, foot[1] - 2, fw, 3, c3)           # sabaton
    rect(g, foot[0] - t // 2, foot[1] - 2, fw, 1, c1)

def torso(g, oy):
    top, belt = V['torso_top'], V['belt_y']
    span = belt - top
    for y in range(top, belt):
        k = (y - top) / span
        x0 = CX - V['back']
        x1 = CX + V['front'] + (V['chest'] if 0.15 <= k <= 0.6 else 0) - (V['waist'] if k > 0.7 else 0)
        wdt = x1 - x0
        for x in range(x0, x1 + 1):
            f = (x - x0) / max(1, wdt)
            c = 'd' if f < 0.2 else 'a' if f < 0.55 else 'h' if f < 0.85 else 'A' if x < x1 else 'H'
            setp(g, x, y + oy, c)
    line(g, CX + V['front'] - 2, top + 2 + oy, CX + V['front'] - 2, belt - 2 + oy, 'H', 1)   # ridge
    bx0, bx1 = CX - V['back'], CX + V['front'] - V['waist']
    rect(g, bx0, belt + oy, bx1 - bx0 + 1, 2, 'G')             # gold belt
    rect(g, bx1 - 2, belt + oy, 2, 2, 'g')
    for i, y in enumerate(range(belt + 2, belt + 2 + V['fauld_h'])):   # faulds
        for x in range(bx0 - i // 2, bx1 + 1 + i // 2):
            c = 'd' if (i % 2 == 1 and x % 3 == 0) or x < CX - 3 else ('a' if x < CX + 2 else 'h')
            setp(g, x, y + oy, c)
    rect(g, CX - V['helm_w'] // 2 + 2, top - 1 + oy, V['helm_w'] - 4, 1, 'd')   # gorget

def pauldron(g, oy):
    rx, ry = V['pauldron']
    sy = V['torso_top'] + 2 + oy
    ell(g, CX + 0.5, sy, rx, ry, lambda x, y: 'H' if y < sy - ry * 0.4 else 'A' if y < sy else 'h')
    ell(g, CX + 0.5, sy + ry + 0.5, rx * 0.8, ry * 0.5, lambda x, y: 'h' if y < sy + ry + 0.5 else 'a')

def helm(g, oy):
    hw, hh, rnd = V['helm_w'], V['helm_h'], V['helm_round']
    x0 = CX - hw // 2; x1 = x0 + hw - 1
    y1 = V['torso_top'] - 2; y0 = y1 - hh + 1
    for y in range(y0, y1 + 1):
        inset = max(0, rnd - (y - y0)) if rnd else 0          # dome: trim the top corners
        for x in range(x0 + inset, x1 - inset + 1):
            f = (x - x0) / max(1, hw - 1)
            c = 'h' if f < 0.22 else 'A' if f < 0.32 else 'H' if f < 0.72 else 'h'
            setp(g, x, y + oy, c)
    slit = y0 + max(3, round(hh * 0.38))
    rect(g, CX, slit + oy, x1 - CX + 1, 1 if hw < 11 else 2, 'V')   # eye slit
    for yy in range(slit + 3, y1 - 1, 2): setp(g, x1 - 1, yy + oy, 'V')   # breaths
    rect(g, x0, y1 + oy, hw, 1, 'd')                            # lower rim

def arm(g, sh, hand):
    t = V['arm_t']
    line(g, sh[0], sh[1], hand[0], hand[1], 'a', t)
    line(g, sh[0], sh[1] - 1, hand[0], hand[1] - 1, 'h', 1)
    gauntlet(g, hand)

def gauntlet(g, hand):
    r = 1.6 + V['arm_t'] * 0.2
    ell(g, hand[0], hand[1], r, r, lambda x, y: 'A' if y < hand[1] else 'a')

def sword(g, hand, ang, L):
    dx, dy = math.cos(ang), math.sin(ang)
    px, py = -dy, dx
    hx, hy = hand
    bx, by = hx + dx * 3, hy + dy * 3
    tx, ty = hx + dx * L, hy + dy * L
    line(g, bx, by, tx - dx * 2, ty - dy * 2, 'W', 2)           # blade
    line(g, bx + px * 1.2, by + py * 1.2, tx - dx * 2 + px * 1.2, ty - dy * 2 + py * 1.2, 'w', 1)
    line(g, tx - dx * 2, ty - dy * 2, tx, ty, 'W', 1)           # point
    line(g, hx + dx * 2 + px * 3, hy + dy * 2 + py * 3, hx + dx * 2 - px * 3, hy + dy * 2 - py * 3, 'G', 2)  # crossguard
    line(g, hx - dx * 1, hy - dy * 1, hx + dx * 1, hy + dy * 1, 'B', 2)   # grip
    line(g, hx - dx * 3, hy - dy * 3, hx - dx * 2, hy - dy * 2, 'G', 2)   # pommel

def arc(g, cx, cy, r, a0, a1, maxt):
    """Crescent swoosh, thickest at the blade end (a1). Painted into empty pixels only."""
    for k in range(241):
        p = k / 240
        a = a0 + (a1 - a0) * p
        t = max(1, round(maxt * p ** 0.7))
        for d in range(t):
            x = int(round(cx + math.cos(a) * (r - d))); y = int(round(cy + math.sin(a) * (r - d) + DY))
            if 0 <= x < W and 0 <= y < H and g[y][x] == '.':
                g[y][x] = 'W' if d == 0 and t > 2 else ('t' if d == t - 1 else 'T')

# ---------------------------------------------------------------- poses
def stances():
    k = V['knee_y']
    raw = {
        'idle':  ((3, k), (4, FOOT), (-3, k), (-4, FOOT)),
        'w0':    ((5, k), (8, FOOT), (-4, k), (-7, FOOT)),
        'w1':    ((2, k), (2, FOOT), (-1, k), (-2, FOOT)),
        'w2':    ((-3, k), (-6, FOOT), (4, k), (7, FOOT)),
        'lunge': ((6, k), (9, FOOT), (-5, k + 1), (-9, FOOT)),
    }
    return {n: tuple((CX + sk(dx), y) for dx, y in pts) for n, pts in raw.items()}

def build(stance, oy=0, sway=0, hand=(0, 0), ang=0, L=20, swoosh=None, sword_behind=False):
    """hand is relative to the shoulder; swoosh = (radius, a0, a1, max thickness) around the shoulder."""
    g = blank()
    near_k, near_f, far_k, far_f = stances()[stance]
    hip = (CX, hip_y() + oy)
    cape(g, oy, sway)
    leg(g, (hip[0] - 2, hip[1]), (far_k[0], far_k[1] + oy), far_f, near=False)
    torso(g, oy)
    leg(g, (hip[0] + 1, hip[1]), (near_k[0], near_k[1] + oy), near_f, near=True)
    sh = shoulder(oy)
    hand = (sk(hand[0]), sk(hand[1])) if not sword_behind else (sk(hand[0]), hand[1])
    L = sk(L)
    if swoosh: swoosh = (sk(swoosh[0]),) + tuple(swoosh[1:3]) + (max(2, sk(swoosh[3])),)
    hd = (sh[0] + hand[0], sh[1] + hand[1])
    if swoosh: arc(g, sh[0], sh[1], *swoosh)
    if sword_behind:                      # overhead: arm and blade go behind the helm
        line(g, sh[0], sh[1], hd[0], hd[1], 'a', V['arm_t'])
        sword(g, hd, ang, L)
        helm(g, oy)
        pauldron(g, oy)
        gauntlet(g, hd)
    else:
        helm(g, oy)
        pauldron(g, oy)
        arm(g, sh, hd)
        sword(g, hd, ang, L)
    return outline(g)

R = math.radians
def frames():
    head = V['torso_top'] - 1 - V['helm_h']   # helm top, used to keep the wind-up blade on canvas
    up = -(sk(4) + V['torso_top'] - head) - 1  # hand just above the helm
    return {
        'idle':   build('idle', hand=(8, 5), ang=R(-78)),
        'walk_1': build('w0', 0, 0, hand=(8, 5), ang=R(-60)),
        'walk_2': build('w1', 1, 1, hand=(7, 6), ang=R(-64)),
        'walk_3': build('w2', 0, 2, hand=(6, 5), ang=R(-68)),
        'walk_4': build('w1', 1, 1, hand=(7, 6), ang=R(-64)),
        'slash_1': build('lunge', hand=(7, up), ang=R(-162), L=20, sword_behind=True),
        'slash_2': build('lunge', hand=(11, -1), ang=R(-3), L=20, swoosh=(31, R(-66), R(-3), 6)),
        'slash_3': build('lunge', hand=(9, 5), ang=R(40), L=18, swoosh=(28, R(-30), R(36), 3)),
    }

def to_img(g, mirror=False):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    for y in range(H):
        for x in range(W):
            c = g[y][x]
            if c == '.': continue
            v = PAL[c].lstrip('#')
            im.putpixel((W - 1 - x if mirror else x, y), tuple(int(v[i:i + 2], 16) for i in (0, 2, 4)) + (255,))
    return im

def sheet(fr, sc=6, pad=8):
    names = list(fr)
    im = Image.new('RGBA', ((W * sc + pad) * len(names) + pad, H * sc + pad * 2), (16, 20, 44, 255))
    for i, n in enumerate(names):
        im.alpha_composite(to_img(fr[n]).resize((W * sc, H * sc), Image.NEAREST), (pad + i * (W * sc + pad), pad))
    return im

def write_game(key):
    global V
    V = VARIANTS[key]
    fr = frames()
    for name, g in fr.items():
        base, _, n = name.partition('_')
        for side, mir in (('right', False), ('left', True)):
            to_img(g, mir).save(os.path.join(OUT, f'hk_{base}_{side}' + (f'_{n}' if n else '') + '.png'))
    helm_top = V['torso_top'] - 1 - V['helm_h'] + DY
    to_img(fr['idle']).crop((CX - 8, helm_top - 1, CX + 8, helm_top + 15)).save(os.path.join(OUT, 'hk_portrait.png'))
    sheet(fr).save(os.path.join(OUT, 'hk_sheet.png'))
    print(f'wrote variant {key} ({V["name"]}) game sprites')

def write_preview():
    """Side-by-side line-up on the Treasury floor at in-game scale (4x), plus a frame sheet per variant."""
    global V
    dest = os.path.join(ROOT, 'knight-options'); os.makedirs(dest, exist_ok=True)
    font = ImageFont.load_default(size=26)
    small = ImageFont.load_default(size=20)
    room = Image.open(os.path.join(ROOT, 'public/assets/rooms/treasury.png')).convert('RGBA')
    S = 4
    crop = room.crop((30, 120, 330, 205))                       # native region around the floor
    bg = crop.resize((crop.width * S, crop.height * S), Image.NEAREST)
    lineup = Image.new('RGBA', (bg.width, bg.height + 60), (12, 18, 38, 255))
    lineup.alpha_composite(bg, (0, 60))
    d = ImageDraw.Draw(lineup)
    old = Image.open(os.path.join(OUT, 'knight_walk_right_1.png'))
    keys = sys.argv[2:] or ['A', 'B', 'C', 'X']
    entries = [('Original', old, 16)] + [(k, None, CX) for k in keys]
    for i, (label, img, cx) in enumerate(entries):
        if img is None:
            V = VARIANTS[label]
            img = to_img(frames()['idle'])
            title = f'{label}: {V["name"]}'
        else:
            title = 'Original (slim)'
        x_native = 18 + i * min(58, 280 // len(entries))                                  # knight centre, native px inside crop
        floor = 196 - 120                                       # floor line inside crop
        big = img.resize((img.width * S, img.height * S), Image.NEAREST)
        lineup.alpha_composite(big, ((x_native - cx) * S, 60 + (floor - img.height) * S))
        tw = d.textlength(title, font=small)
        d.text((x_native * S - tw / 2, 18), title, font=small, fill=(242, 230, 207, 255))
    lineup.convert('RGB').save(os.path.join(dest, 'lineup.png'))
    for k in [k for k in keys if k != 'X']:
        V = VARIANTS[k]
        sh = sheet(frames(), sc=5)
        top = Image.new('RGBA', (sh.width, sh.height + 44), (16, 20, 44, 255))
        top.alpha_composite(sh, (0, 44))
        ImageDraw.Draw(top).text((12, 8), f'Option {k}: {V["name"]}  (idle, walk x4, slash x3)', font=font, fill=(232, 164, 90, 255))
        top.convert('RGB').save(os.path.join(dest, f'option-{k}.png'))
    print('wrote previews to', dest)

if __name__ == '__main__':
    arg = sys.argv[1] if len(sys.argv) > 1 else 'preview'
    if arg == 'preview': write_preview()
    elif arg in VARIANTS: write_game(arg)
    else: sys.exit(f'unknown variant {arg!r}; choose preview or one of {", ".join(VARIANTS)}')
