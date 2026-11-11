"""Throne Room: a lower-seated, grander throne (so the seated knight's feet reach the dais),
plus more gold: gilded step edges, two gold candelabra and a gold-fringed carpet.
Usage: python3 tools/throne_art.py preview | write
Starts from tools/rooms_base/throne.png and re-applies the banner runes."""
import sys
sys.path.insert(0, 'tools')
from PIL import Image
import banner_runes

K = (8, 10, 24)
G = [(96, 60, 14), (150, 100, 26), (214, 150, 46), (255, 210, 122), (255, 240, 190)]
R = [(58, 18, 28), (106, 36, 52), (148, 56, 76), (190, 80, 96)]
GEM_R = [(90, 10, 30), (210, 40, 70), (255, 150, 170)]
GEM_B = [(20, 40, 110), (60, 110, 220), (170, 210, 255)]
CX = 180                  # throne centre
SEAT = 174                # seat top: the seated knight's thighs (sprite top 154, feet on the dais at 184)
KNIGHT_TOP = 154

class C:
    def __init__(s, im): s.px = im.load()
    def p(s, x, y, c): s.px[x, y] = c + (255,)
    def r(s, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1): s.p(x, y, c)
    def out(s, x0, y0, x1, y1, fill):
        s.r(x0, y0, x1, y1, K); s.r(x0 + 1, y0 + 1, x1 - 1, y1 - 1, fill)

def gem(c, x, y, pal):
    c.r(x - 1, y - 1, x + 1, y + 1, K)
    c.p(x, y, pal[1]); c.p(x - 1, y, pal[1]); c.p(x + 1, y, pal[0]); c.p(x, y - 1, pal[2]); c.p(x, y + 1, pal[0])

def gold_bar(c, x0, y0, x1, y1):
    """bevelled gold block with outline"""
    c.out(x0, y0, x1, y1, G[2])
    c.r(x0 + 1, y0 + 1, x1 - 1, y0 + 1, G[3]); c.r(x0 + 1, y0 + 1, x0 + 1, y1 - 1, G[3])
    c.r(x0 + 1, y1 - 1, x1 - 1, y1 - 1, G[1]); c.r(x1 - 1, y0 + 1, x1 - 1, y1 - 1, G[1])

def pinnacle(c, x, ytop, ybot):
    for y in range(ytop, ybot + 1):
        hw = 0 if y < ytop + 2 else 1 if y < ytop + 5 else 2
        c.r(x - hw - 1, y, x + hw + 1, y, K)
        c.r(x - hw, y, x + hw, y, G[2]); c.p(x - hw, y, G[3])
        if hw: c.p(x + hw, y, G[1])
    c.p(x, ytop - 1, K); c.p(x, ytop - 2, G[4])

def throne(c):
    x0, x1 = CX - 18, CX + 18                       # 37 wide back (covers the old throne)
    top = 108
    # back panel: gold frame, red velvet, quilted gold studs
    gold_bar(c, x0, top, x1, SEAT)
    c.r(x0 + 3, top + 3, x1 - 3, SEAT - 1, K)
    c.r(x0 + 4, top + 4, x1 - 4, SEAT - 1, R[1])
    for y in range(top + 4, SEAT):
        for x in range(x0 + 4, x1 - 3):
            if (x + y) % 6 == 0: c.p(x, y, R[0])
            elif (x - y) % 6 == 0: c.p(x, y, R[0])
    for y in range(top + 7, SEAT - 2, 6):
        for x in range(x0 + 7 + ((y - top) // 6 % 2) * 3, x1 - 5, 6): c.p(x, y, G[3])
    c.r(x0 + 4, top + 4, x0 + 4, SEAT - 1, R[2])     # velvet sheen
    # crest: gothic gold arch with crown and gems
    for i in range(22):
        y = top - 1 - i
        hw = 18 - (i * i) // 26
        if hw < 1: break
        c.r(CX - hw - 1, y, CX + hw + 1, y, K)
        c.r(CX - hw, y, CX + hw, y, G[2] if i % 4 else G[3])
        c.p(CX - hw, y, G[3]); c.p(CX + hw, y, G[1])
    # crown on the crest
    cy = top - 12
    c.r(CX - 6, cy - 1, CX + 6, cy + 3, K); c.r(CX - 5, cy, CX + 5, cy + 2, G[3])
    for dx in (-5, 0, 5):
        c.r(CX + dx - 1, cy - 5, CX + dx + 1, cy - 1, K); c.r(CX + dx, cy - 4, CX + dx, cy - 1, G[3]); c.p(CX + dx, cy - 5, G[4])
    gem(c, CX, cy + 1, GEM_R)
    gem(c, CX, top + 6, GEM_B); gem(c, x0 + 6, top + 6, GEM_R); gem(c, x1 - 6, top + 6, GEM_R)
    # side pinnacles
    pinnacle(c, x0 - 1, top - 12, SEAT - 6); pinnacle(c, x1 + 1, top - 12, SEAT - 6)
    gem(c, x0 - 1, top + 10, GEM_B); gem(c, x1 + 1, top + 10, GEM_B)
    # armrests (low, beside the knight's hips) with lion-paw scroll ends
    for (a0, a1, end) in ((x0 - 5, x0 + 4, x0 - 5), (x1 - 4, x1 + 5, x1 + 5)):
        gold_bar(c, a0, SEAT - 7, a1, SEAT - 3)
        c.r(end - 1, SEAT - 9, end + 1, SEAT - 6, K); c.p(end, SEAT - 8, G[3]); c.p(end, SEAT - 7, G[2])
        gem(c, (a0 + a1) // 2, SEAT - 5, GEM_R)
    # seat cushion + skirt + carved gold feet down to the dais (y 183)
    gold_bar(c, x0 - 2, SEAT, x1 + 2, SEAT + 2)
    c.out(x0, SEAT + 3, x1, 183, R[1])
    c.r(x0 + 1, SEAT + 3, x1 - 1, SEAT + 3, R[2])
    for x in range(x0 + 2, x1 - 1, 3): c.p(x, SEAT + 4, G[2])        # gold fringe
    for fx in (x0 - 1, x1 - 3):
        gold_bar(c, fx, SEAT + 3, fx + 4, 183)
        c.p(fx + 2, 180, G[4])

def steps_gold(c):
    # gilded nosing on the two dais steps (rows 184 and 188 are the step tops)
    for (y, xa, xb) in ((184, 149, 210), (188, 142, 218)):
        c.r(xa, y, xb, y, G[2])
        for x in range(xa, xb + 1, 2): c.p(x, y, G[3])
        c.r(xa, y + 1, xb, y + 1, G[0])

def candelabra(c, x, floor):
    """tall gold candelabrum: base, stem with knops, three-branch top, candles"""
    gold_bar(c, x - 4, floor - 3, x + 4, floor)
    for y in range(floor - 30, floor - 3):
        c.r(x - 2, y, x + 2, y, K); c.p(x - 1, y, G[3]); c.p(x, y, G[2]); c.p(x + 1, y, G[1])
    for ky in (floor - 10, floor - 20):
        c.r(x - 3, ky - 1, x + 3, ky + 1, K); c.r(x - 2, ky, x + 2, ky, G[3])
    arm = floor - 31
    c.r(x - 8, arm - 1, x + 8, arm + 1, K); c.r(x - 7, arm, x + 7, arm, G[2])
    for dx in (-7, 0, 7):
        c.r(x + dx - 2, arm - 3, x + dx + 2, arm - 1, K); c.r(x + dx - 1, arm - 2, x + dx + 1, arm - 2, G[3])
        c.r(x + dx - 1, arm - 8, x + dx + 1, arm - 3, K); c.r(x + dx, arm - 7, x + dx, arm - 3, (236, 228, 208))
        c.p(x + dx, arm - 9, (255, 210, 122)); c.p(x + dx, arm - 10, (255, 250, 220))

def carpet_gold(c, im):
    px = im.load()
    for x in range(150, 211):
        if px[x, 197][0] > px[x, 197][2] + 30: c.p(x, 197, G[2] if x % 2 else G[3])
    for x in (150, 151, 209, 210):
        for y in range(197, 200): c.p(x, y, G[2])

def build():
    im = Image.open('tools/rooms_base/throne.png').convert('RGBA')
    c = C(im)
    steps_gold(c)
    throne(c)
    candelabra(c, 146, 191); candelabra(c, 214, 191)
    carpet_gold(c, im)
    return banner_runes.apply(im, 'throne', 'C')

if __name__ == '__main__':
    after = build()
    if sys.argv[1] == 'preview':
        knight = Image.open('public/assets/sprites/knight_seated_front.png').convert('RGBA')
        before = Image.open('public/assets/rooms/throne.png').convert('RGBA'); before.alpha_composite(knight, (169, 146))
        a2 = after.copy(); a2.alpha_composite(knight, (169, KNIGHT_TOP))
        box = (100, 70, 260, 205); w, h = box[2] - box[0], box[3] - box[1]
        out = Image.new('RGBA', (w * 8 + 16, h * 4), (0, 0, 0, 255))
        out.paste(before.crop(box).resize((w * 4, h * 4), Image.NEAREST), (0, 0))
        out.paste(a2.crop(box).resize((w * 4, h * 4), Image.NEAREST), (w * 4 + 16, 0))
        out.save('sign-options/throne-redesign.png')
        a2.resize((1440, 900), Image.NEAREST).save('sign-options/throne-full.png')
    else:
        after.save('public/assets/rooms/throne.png')
