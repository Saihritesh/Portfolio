"""The Dread Wyrm: final boss of the Courtyard Siege, designed at native resolution.

Usage:
  python3 tools/wyrm_art.py preview   # sheet + battle mock-up -> arena-options/ (game untouched)
  python3 tools/wyrm_art.py write     # boss_{pose}_{right,left}.png -> public/assets/sprites/

Faces right. Canvas 160x112 native (shown at 4x like everything else).
Built from a spine curve (round, moonlit body with scales and molten belly plates),
an angular horned head, bat wings with finger bones and torn membrane, dorsal spikes,
a bladed tail and clawed legs.
"""
import math, os, sys
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from arena_art import ROOT, hx, C, outline, mirror, courtyard, fireball, heart, fbm, RW, RH, FLOOR

W, H = 160, 112
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
HIDE = [hx(c) for c in ('#1A1934', '#3A3860', '#6A6890', '#9A98BC', '#C4C2DC', '#E4E2F0', '#FAF8FF')]   # white hide, cool moonlit shadows
MEMB = [hx(c) for c in ('#2A2840', '#4A4868', '#6E6C94', '#9894B8', '#BEBAD8', '#DCDAEE')]
BONE = [hx(c) for c in ('#07060F', '#141226', '#26244A', '#3E3C72', '#5E5C9A')]    # obsidian horns, spikes, claws
CRUST = [hx(c) for c in ('#1E0C08', '#3A1A12', '#5A2614')]
MAGMA = [hx(c) for c in ('#B8641E', '#E89A3C', '#FFC872', '#FFF3C4')]
GLOW = set(MAGMA)

def ramp(cols, v, x, y):
    v = max(0.0, min(0.999, v)) * (len(cols) - 1)
    i = int(v); f = v - i
    return cols[min(i + 1, len(cols) - 1)] if f * 16 > BAYER[y % 4][x % 4] else cols[i]

def catmull(pts, n=20):
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t * t
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t ** 3) for j in range(len(p1))))
    out.append(tuple(pts[-1]))
    return out

class Canvas:
    def __init__(self):
        self.im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); self.px = self.im.load(); self.d = ImageDraw.Draw(self.im)
    def set(self, x, y, c):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < W and 0 <= y < H: self.px[x, y] = c
    def get(self, x, y):
        return self.px[x, y] if 0 <= x < W and 0 <= y < H else (0, 0, 0, 0)

# ---------------------------------------------------------------- body
def tube(cv, pts, belly=True, glow=0.0, scales=True):
    """Round body along a spine. Lit from above (the moon); underside is armoured belly plates
    with molten seams. glow (0..1) brightens the seams (e.g. while breathing)."""
    S = catmull(pts, 24)
    along = 0.0
    spine = []
    for i, (sx, sy, r) in enumerate(S):
        if i: along += math.hypot(sx - S[i - 1][0], sy - S[i - 1][1])
        a, b = S[max(i - 1, 0)], S[min(i + 1, len(S) - 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]; tl = math.hypot(tx, ty) or 1
        nx, ny = -ty / tl, tx / tl
        if ny > 0: nx, ny = -nx, -ny                            # normal points up, toward the moon
        spine.append((sx, sy, r, along, nx, ny))
    for sx, sy, r, al, nx, ny in spine:
        for yy in range(int(sy - r) - 1, int(sy + r) + 2):
            for xx in range(int(sx - r) - 1, int(sx + r) + 2):
                ox, oy = xx - sx, yy - sy
                if ox * ox + oy * oy > r * r: continue
                p = (ox * nx + oy * ny) / max(r, 1)              # 1 = top edge, -1 = underside
                if belly and p < -0.42:
                    seam = (al + ox * 0.15) % 4.2 < 1.0
                    heat = glow + max(0, 1 - abs(al - 70) / 60) * 0.35   # hottest at the chest
                    if seam: c = ramp(MAGMA, 0.2 + heat * 0.8 + (fbm(xx, yy, 7, 3) - 0.5) * 0.3, xx, yy)
                    else: c = ramp(CRUST, 0.35 + (p + 1) * 0.6 + heat * 0.3, xx, yy)
                else:
                    v = 0.18 + 0.5 * ((p + 1) / 2) ** 1.4 + (fbm(xx, yy, 3, 4) - 0.5) * 0.12
                    if scales:                                   # overlapping scale crescents
                        row = int((p + 1) * r / 2.2)
                        cell = (al + (row % 2) * 1.6) % 3.2
                        if cell < 0.9: v -= 0.12
                        elif cell < 1.6 and p > -0.2: v += 0.08
                    if p > 0.82: v = 0.86                        # moonlit rim
                    c = ramp(HIDE, v, xx, yy)
                cv.set(xx, yy, c)
    return spine

def spikes(cv, spine, start, end, every, size, lean=0.7):
    """Dorsal spikes along the top edge of a spine between distances start..end."""
    nxt = start
    for sx, sy, r, al, nx, ny in spine:
        if al < nxt or al > end: continue
        nxt += every
        t = (al - start) / max(1, end - start)
        L = size(t)
        bx, by = sx + nx * (r - 0.5), sy + ny * (r - 0.5)
        tx, ty = -ny, nx                                        # tangent (pointing toward the tail)
        if tx > 0: tx, ty = -tx, -ty
        ax, ay = bx + nx * L + tx * L * lean, by + ny * L + ty * L * lean
        base = [(bx - tx * 2, by - ty * 2), (bx + tx * 2, by + ty * 2)]
        cv.d.polygon([base[0], (ax, ay), base[1]], fill=BONE[1])
        cv.d.line([base[0], (ax, ay)], fill=BONE[3])          # lit leading edge

# ---------------------------------------------------------------- wings
def wing(cv, shoulder, elbow, wrist, tips, hip, far=False):
    dark = 0.25 if far else 0.0
    # membrane: shoulder -> wrist -> fingertips with scalloped trailing edge -> hip
    poly = [shoulder, elbow, wrist]
    for i, t in enumerate(tips):
        poly.append(t)
        nxt = tips[i + 1] if i + 1 < len(tips) else hip
        mx, my = (t[0] + nxt[0]) / 2, (t[1] + nxt[1]) / 2
        poly.append((mx + (wrist[0] - mx) * 0.28, my + (wrist[1] - my) * 0.28))   # scallop pulls toward the wrist
    poly.append(hip)
    mask = Image.new('L', (W, H), 0); ImageDraw.Draw(mask).polygon(poly, fill=255); mp = mask.load()
    for y in range(H):
        for x in range(W):
            if not mp[x, y]: continue
            dw = math.hypot(x - wrist[0], y - wrist[1])
            # translucent membrane: moonlight shows through, brightest between the fingers
            v = 0.78 - dw / 170 - dark + (fbm(x, y, 21, 5) - 0.5) * 0.18
            cv.set(x, y, ramp(MEMB, v, x, y))
    if not far:
        for i in range(len(tips)):
            sx_, sy_ = poly[4 + i * 2] if 4 + i * 2 < len(poly) - 1 else hip
            for k in range(1, 12):
                t = k / 12; x = wrist[0] + (sx_ - wrist[0]) * t; y = wrist[1] + (sy_ - wrist[1]) * t
                if mp[int(min(W - 1, max(0, x))), int(min(H - 1, max(0, y)))] and k % 2: cv.set(x, y, MEMB[1])
    # tears in the membrane
    if not far:
        for i, t in enumerate(tips[1:3]):
            hxp, hyp = (t[0] * 0.6 + wrist[0] * 0.4), (t[1] * 0.6 + wrist[1] * 0.4) + 3
            for yy in range(-2, 3):
                for xx in range(-2 + abs(yy) // 2, 3 - abs(yy) // 2):
                    if mp[int(min(W - 1, max(0, hxp + xx))), int(min(H - 1, max(0, hyp + yy)))]:
                        cv.set(hxp + xx, hyp + yy, (0, 0, 0, 0))
    # bones: arm (thick) then fingers, lit along their top
    bc = (BONE[0], BONE[1]) if far else (BONE[1], BONE[2])
    for a, b, w in ((shoulder, elbow, 4), (elbow, wrist, 3)):
        cv.d.line([a, b], fill=HIDE[2] if far else HIDE[3], width=w)
        cv.d.line([(a[0], a[1] - 1), (b[0], b[1] - 1)], fill=HIDE[4] if not far else HIDE[3], width=1)
    for t in tips:
        cv.d.line([wrist, t], fill=HIDE[1] if far else HIDE[2], width=2)
        cv.d.line([(wrist[0], wrist[1] - 1), (t[0], t[1] - 1)], fill=HIDE[2] if far else HIDE[4], width=1)
        cv.set(t[0], t[1], bc[1])                                 # claw at each fingertip
    # wrist claw
    cv.d.polygon([(wrist[0], wrist[1] - 1), (wrist[0] + 4, wrist[1] - 5), (wrist[0] + 2, wrist[1] + 1)], fill=BONE[3] if not far else BONE[1])

WING_POSES = {   # elbow, wrist, fingertips (leading -> trailing)
    'up':   ((84, 26), (100, 6),  [(76, 1), (56, 6), (42, 20), (48, 40)]),
    'mid':  ((80, 36), (102, 26), [(86, 4), (60, 10), (40, 26), (48, 46)]),
    'down': ((82, 70), (100, 90), [(82, 106), (62, 102), (48, 88), (54, 72)]),
}

# ---------------------------------------------------------------- head
def head(cv, hx0, hy0, open_jaw=False):
    # far horn first (behind the skull)
    horn(cv, hx0 + 2, hy0 - 6, far=True)
    upper = [(hx0 - 5, hy0 - 4), (hx0 + 2, hy0 - 9), (hx0 + 12, hy0 - 9), (hx0 + 22, hy0 - 4), (hx0 + 29, hy0 + 1),
             (hx0 + 29, hy0 + 4), (hx0 + 18, hy0 + 5), (hx0 + 6, hy0 + 6), (hx0 - 4, hy0 + 7)]
    jaw_drop = 9 if open_jaw else 0
    lower = [(hx0 - 4, hy0 + 6), (hx0 + 6, hy0 + 7 + jaw_drop * 0.3), (hx0 + 18, hy0 + 8 + jaw_drop * 0.8),
             (hx0 + 25, hy0 + 8 + jaw_drop), (hx0 + 22, hy0 + 11 + jaw_drop), (hx0 + 6, hy0 + 13 + jaw_drop * 0.5), (hx0 - 4, hy0 + 11)]
    if open_jaw:                                                # glowing maw between the jaws
        cv.d.polygon([(hx0 + 2, hy0 + 6), (hx0 + 27, hy0 + 4), (hx0 + 24, hy0 + 9 + jaw_drop), (hx0 + 4, hy0 + 10)], fill=MAGMA[0])
        cv.d.polygon([(hx0 + 6, hy0 + 7), (hx0 + 24, hy0 + 6), (hx0 + 21, hy0 + 8 + jaw_drop * 0.8), (hx0 + 8, hy0 + 9)], fill=MAGMA[1])
        cv.d.polygon([(hx0 + 10, hy0 + 7), (hx0 + 22, hy0 + 7), (hx0 + 18, hy0 + 7 + jaw_drop * 0.6)], fill=MAGMA[2])
    # lower jaw
    mask = Image.new('L', (W, H), 0); ImageDraw.Draw(mask).polygon(lower, fill=255); mp = mask.load()
    for y in range(H):
        for x in range(W):
            if mp[x, y]: cv.set(x, y, ramp(HIDE, 0.25 + (0.15 if y < hy0 + 9 + jaw_drop * 0.5 else 0), x, y))
    # skull: lit top plane, darker cheek, heavy brow
    mask = Image.new('L', (W, H), 0); ImageDraw.Draw(mask).polygon(upper, fill=255); mp = mask.load()
    for y in range(H):
        for x in range(W):
            if not mp[x, y]: continue
            top_plane = y < hy0 - 3 + (x - hx0) * 0.22
            v = 0.62 if top_plane else 0.3 + (fbm(x, y, 9, 3) - 0.5) * 0.15
            if top_plane and y <= hy0 - 8 + (x - hx0) * 0.22: v = 0.85
            cv.set(x, y, ramp(HIDE, v, x, y))
    cv.d.line([(hx0 + 2, hy0 - 4), (hx0 + 15, hy0 - 3)], fill=HIDE[0], width=2)          # brow ridge shadow
    # teeth along both jaws
    for x in range(hx0 + 6, hx0 + 27, 3):
        cv.set(x, hy0 + 5 + (x - hx0) * -0.02, hx('#FFFFFF')); cv.set(x, hy0 + 6, HIDE[1])
        if open_jaw: cv.set(x + 1, hy0 + 7 + jaw_drop * ((x - hx0) / 30), hx('#FFFFFF'))
    # eye: white-hot with a dithered glow
    ex, ey = hx0 + 11, hy0 - 2
    for yy in range(-3, 4):
        for xx in range(-4, 5):
            if (xx + yy) % 2 == 0 and xx * xx + yy * yy * 2 < 16 and cv.get(ex + xx, ey + yy)[3]:
                cv.set(ex + xx, ey + yy, MAGMA[0])
    cv.set(ex - 1, ey, MAGMA[1]); cv.set(ex, ey, MAGMA[3]); cv.set(ex + 1, ey, MAGMA[2]); cv.set(ex + 2, ey, MAGMA[1])
    cv.set(hx0 + 26, hy0 - 1, MAGMA[1])                                                   # smouldering nostril
    # cheek spikes swept back
    for i, (bx, by) in enumerate(((hx0 - 3, hy0 + 2), (hx0 - 3, hy0 + 6), (hx0 - 2, hy0 + 10))):
        L = 6 - i
        cv.d.polygon([(bx, by - 1), (bx - L, by + 1 + i), (bx, by + 2)], fill=BONE[1])
        cv.set(bx - L, by + 1 + i, BONE[3])
    horn(cv, hx0, hy0 - 7)

def horn(cv, bx, by, far=False):
    """A big horn sweeping back and curling up."""
    pts = [(bx, by, 3.2), (bx - 9, by - 3, 2.6), (bx - 17, by - 3, 2.0), (bx - 23, by - 8, 1.4), (bx - 24, by - 15, 0.8)]
    for i, (x, y, r) in enumerate(catmull(pts, 10)):
        for yy in range(int(y - r) - 1, int(y + r) + 2):
            for xx in range(int(x - r) - 1, int(x + r) + 2):
                if (xx - x) ** 2 + (yy - y) ** 2 <= r * r:
                    v = 0.75 if yy < y - r * 0.2 else 0.4
                    if far: v -= 0.35
                    v += i * 0.004
                    cv.set(xx, yy, ramp(BONE, v, xx, yy))

def leg(cv, hip, knee, foot, far=False):
    col = HIDE[1] if far else HIDE[2]
    cv.d.ellipse((hip[0] - 6, hip[1] - 5, hip[0] + 5, hip[1] + 6), fill=col)                   # thigh
    cv.d.line([hip, knee], fill=col, width=8 if not far else 6)
    cv.d.line([knee, foot], fill=col, width=5 if not far else 4)
    cv.d.line([(hip[0], hip[1] - 2), (knee[0], knee[1] - 2)], fill=HIDE[3] if not far else HIDE[2], width=1)
    for dx in (-2, 0, 2):                                        # talons
        cv.d.line([(foot[0] + dx, foot[1]), (foot[0] + dx + 2, foot[1] + 3)], fill=BONE[3] if not far else BONE[1], width=1)

# ---------------------------------------------------------------- assemble
POSES = {'fly1': 'up', 'fly2': 'mid', 'fly3': 'down', 'breathe': 'mid'}
def wyrm(pose):
    cv = Canvas()
    wstate = POSES[pose]
    bob = {'up': 2, 'mid': 0, 'down': -2}[wstate]
    breathe = pose == 'breathe'
    def b(p): return (p[0], p[1] + bob) + tuple(p[2:])
    spine_pts = [b(p) for p in [(8, 64, 1.2), (14, 76, 2.4), (26, 84, 4), (42, 80, 6.5), (58, 70, 10), (74, 64, 13.5),
                                (90, 62, 14), (102, 56, 10.5), (110, 46, 8), (118, 38, 7)]]
    elbow, wrist, tips = WING_POSES[wstate]
    shoulder, hip = b((88, 54)), b((64, 62))
    # far wing, far legs
    wing(cv, (shoulder[0] + 6, shoulder[1] - 3), (elbow[0] + 8, elbow[1] - 4), (wrist[0] + 8, wrist[1] - 3),
         [(x + 8, y - 3) for x, y in tips], (hip[0] + 6, hip[1] - 2), far=True)
    leg(cv, b((70, 72)), b((64, 82)), b((70, 90)), far=True)
    leg(cv, b((98, 70)), b((104, 78)), b((110, 84)), far=True)
    # tail blade
    tx, ty = spine_pts[0][0], spine_pts[0][1]
    cv.d.polygon([(tx + 2, ty + 2), (tx - 6, ty - 8), (tx - 1, ty - 1), (tx - 8, ty + 2), (tx + 1, ty + 4)], fill=BONE[1])
    cv.d.line([(tx + 2, ty + 2), (tx - 6, ty - 8)], fill=BONE[3])
    spine = tube(cv, spine_pts, glow=0.6 if breathe else 0.0)
    spikes(cv, spine, 18, 150, 6.5, lambda t: 3 + 7 * math.sin(min(1, t * 1.25) * math.pi * 0.9), lean=0.8)
    # near legs
    leg(cv, b((62, 74)), b((54, 84)), b((60, 94)))
    leg(cv, b((92, 72)), b((98, 82)), b((104, 88)))
    # head at the end of the neck
    hx0, hy0 = int(spine_pts[-1][0]) + 2, int(spine_pts[-1][1]) - 2
    head(cv, hx0, hy0, open_jaw=breathe)
    # near wing last, over the body
    wing(cv, shoulder, b(elbow), b(wrist), [b(t) for t in tips], hip)
    return outline(cv.im, skip=tuple(GLOW))

MOUTH = (148, 38)   # where fire leaves the jaws (right-facing, breathe pose), for the game code

def preview():
    dest = os.path.join(ROOT, 'arena-options'); os.makedirs(dest, exist_ok=True)
    S = 4
    small = ImageFont.load_default(size=18); big_f = ImageFont.load_default(size=24)
    poses = ['fly1', 'fly2', 'fly3', 'breathe']
    frames = [wyrm(p) for p in poses]
    kn = Image.open(os.path.join(ROOT, 'public/assets/sprites/hk_idle_right.png'))
    items = frames + [kn]
    sheet = Image.new('RGBA', (sum(i.width * S + 24 for i in items) + 24, H * S + 70), (16, 20, 44, 255))
    x = 24
    for i, im in enumerate(items):
        sheet.alpha_composite(im.resize((im.width * S, im.height * S), Image.NEAREST), (x, 50 + (H - im.height) * S))
        ImageDraw.Draw(sheet).text((x, 14), (poses + ['knight (scale)'])[i], font=small, fill=(232, 164, 90, 255))
        x += im.width * S + 24
    sheet.convert('RGB').save(os.path.join(dest, 'boss-wyrm-sheet.png'))
    # battle mock-up
    scene = courtyard()
    scene.alpha_composite(mirror(frames[3]), (170, 2))
    fb, fb2 = fireball(0), fireball(1)
    for x, y, f in ((150, 60, fb), (110, 100, fb2), (176, 126, fb), (220, 140, fb2), (66, 150, fb)):
        scene.alpha_composite(f, (x, y))
    scene.alpha_composite(Image.open(os.path.join(ROOT, 'public/assets/sprites/hk_walk_right_1.png')), (96 - 22, FLOOR - 60 - 18))
    big = scene.resize((RW * S, RH * S), Image.NEAREST)
    h = ImageDraw.Draw(big)
    for i in range(5):
        hh = heart(i < 3); big.alpha_composite(hh.resize((hh.width * S, hh.height * S), Image.NEAREST), (28 + i * 40, 28))
    h.rectangle((380, 20, 1060, 92), fill=(5, 7, 15, 200), outline=(58, 74, 117, 255), width=3)
    h.text((720, 30), 'THE DREAD WYRM', font=big_f, anchor='mt', fill=(232, 164, 90, 255))
    h.rectangle((400, 64, 1040, 80), fill=(22, 29, 51, 255), outline=(4, 6, 15, 255), width=3)
    h.rectangle((403, 67, 403 + int(634 * 0.82), 77), fill=(208, 74, 94, 255))
    big.convert('RGB').save(os.path.join(dest, 'boss-wyrm.png'))
    print('wrote', os.path.join(dest, 'boss-wyrm.png'))

def write():
    out = os.path.join(ROOT, 'public/assets/sprites')
    for p in POSES:
        im = wyrm(p)
        im.save(os.path.join(out, f'boss_{p}_right.png')); mirror(im).save(os.path.join(out, f'boss_{p}_left.png'))
    print('wrote boss sprites')

if __name__ == '__main__':
    {'preview': preview, 'write': write}.get(sys.argv[1] if len(sys.argv) > 1 else 'preview', preview)()
