"""The Trophy Room: built on the Chronicle Hall shell (pillars, doors, torches), with the three
tapestries replaced by a certificate board, a glass trophy cabinet and a course-medal board.
Usage: python3 tools/trophy_art.py preview | write"""
import sys, random
from PIL import Image

K = (8, 10, 24)
WOOD = [(34, 20, 14), (58, 36, 22), (84, 54, 32), (112, 72, 42), (148, 100, 58)]
GOLD = [(96, 60, 14), (150, 100, 26), (214, 150, 46), (255, 210, 122)]
PARCH = [(120, 104, 80), (170, 156, 128), (212, 202, 178), (236, 228, 208)]
SEAL = [(70, 18, 28), (130, 34, 48), (190, 64, 78)]
GLASS = [(10, 14, 30), (16, 22, 46), (26, 34, 66)]
GLINT = (110, 130, 180)
RIBBONS = [((40, 70, 140), (80, 120, 200)), ((120, 30, 44), (190, 64, 78)), ((30, 100, 70), (70, 160, 110)), ((110, 70, 160), (170, 130, 230))]

class Canvas:
    def __init__(self, im): self.im = im; self.px = im.load()
    def p(self, x, y, c): self.px[x, y] = c + (255,)
    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1): self.p(x, y, c)
    def box(self, x0, y0, x1, y1, fill, light, dark, outline=K):
        self.rect(x0, y0, x1, y1, outline)
        self.rect(x0 + 1, y0 + 1, x1 - 1, y1 - 1, fill)
        self.rect(x0 + 1, y0 + 1, x1 - 1, y0 + 1, light); self.rect(x0 + 1, y0 + 1, x0 + 1, y1 - 1, light)
        self.rect(x0 + 1, y1 - 1, x1 - 1, y1 - 1, dark); self.rect(x1 - 1, y0 + 1, x1 - 1, y1 - 1, dark)

def panel(c, x0, y0, x1, y1):
    """dark wooden display board with planks and gold corner caps"""
    c.box(x0, y0, x1, y1, WOOD[1], WOOD[3], WOOD[0])
    for x in range(x0 + 9, x1 - 2, 9):
        for y in range(y0 + 2, y1 - 1): c.p(x, y, WOOD[0])
        for y in range(y0 + 2, y1 - 1, 3): c.p(x + 1, y, WOOD[2])
    rng = random.Random(x0)
    for _ in range((x1 - x0) * (y1 - y0) // 40):
        c.p(rng.randint(x0 + 2, x1 - 2), rng.randint(y0 + 2, y1 - 2), WOOD[2])
    for (x, y) in ((x0, y0), (x1 - 2, y0), (x0, y1 - 2), (x1 - 2, y1 - 2)):
        c.rect(x, y, x + 2, y + 2, GOLD[2]); c.p(x, y, GOLD[3]); c.p(x + 2, y + 2, GOLD[0])

def certificate(c, x0, y0, w, h, seed):
    x1, y1 = x0 + w - 1, y0 + h - 1
    c.rect(x0, y0, x1, y1, K)
    c.rect(x0 + 1, y0 + 1, x1 - 1, y1 - 1, GOLD[2])
    c.rect(x0 + 1, y0 + 1, x1 - 1, y0 + 1, GOLD[3]); c.rect(x0 + 1, y0 + 1, x0 + 1, y1 - 1, GOLD[3])
    c.rect(x0 + 1, y1 - 1, x1 - 1, y1 - 1, GOLD[0]); c.rect(x1 - 1, y0 + 1, x1 - 1, y1 - 1, GOLD[1])
    c.rect(x0 + 2, y0 + 2, x1 - 2, y1 - 2, GOLD[0])
    c.rect(x0 + 3, y0 + 3, x1 - 3, y1 - 3, PARCH[2])
    c.rect(x0 + 3, y0 + 3, x1 - 3, y0 + 3, PARCH[3])
    rng = random.Random(seed)
    # heading + text lines
    c.rect(x0 + 6, y0 + 6, x1 - 6, y0 + 6, PARCH[0])
    y = y0 + 9
    while y < y1 - 8:
        c.rect(x0 + 5, y, x1 - 5 - rng.randint(0, 4), y, PARCH[1]); y += 2
    # wax seal + ribbon tails
    sx, sy = x1 - 6, y1 - 6
    c.p(sx - 1, sy + 3, SEAL[0]); c.p(sx + 1, sy + 3, SEAL[0]); c.p(sx - 1, sy + 2, SEAL[1]); c.p(sx + 1, sy + 2, SEAL[1])
    for dx in range(-2, 3):
        for dy in range(-2, 2):
            if abs(dx) + abs(dy) <= 3: c.p(sx + dx, sy + dy, SEAL[1])
    c.p(sx - 1, sy - 1, SEAL[2]); c.p(sx, sy, SEAL[0])
    # signature squiggle
    c.p(x0 + 5, y1 - 5, PARCH[0]); c.p(x0 + 6, y1 - 6, PARCH[0]); c.p(x0 + 7, y1 - 5, PARCH[0]); c.p(x0 + 8, y1 - 6, PARCH[0])

def cup(c, cx, by, s=1.0):
    """gold trophy cup standing on y=by, centred on cx"""
    W = round(5 * s); H = round(7 * s)
    top = by - 4 - round(3 * s) - H
    pts = {}
    for i, y in enumerate(range(top, top + H)):       # bowl tapers downwards
        hw = W - (i * W) // (H + 2)
        for x in range(cx - hw, cx + hw + 1): pts[(x, y)] = GOLD[2] if x < cx else GOLD[1]
        pts[(cx - hw, y)] = GOLD[3] if i < H - 1 else GOLD[2]
    for x in range(cx - W, cx + W + 1): pts[(x, top)] = GOLD[3] if x < cx + W else GOLD[2]
    stem = range(top + H, by - 3)
    for y in stem: pts[(cx, y)] = GOLD[2]; pts[(cx + 1, y)] = GOLD[1]
    for x in range(cx - 3, cx + 4): pts[(x, by - 3)] = GOLD[2]; pts[(x, by - 2)] = GOLD[1]
    for x in range(cx - 4, cx + 5): pts[(x, by - 1)] = WOOD[2]; pts[(x, by)] = WOOD[1]
    # handles
    for dy in range(1, max(3, round(4 * s))):
        pts[(cx - W - 2, top + dy)] = GOLD[2]; pts[(cx + W + 2, top + dy)] = GOLD[1]
    pts[(cx - W - 1, top + 1)] = GOLD[2]; pts[(cx + W + 1, top + 1)] = GOLD[1]
    hb = top + max(3, round(4 * s))
    pts[(cx - W - 1, hb)] = GOLD[2]; pts[(cx + W + 1, hb)] = GOLD[1]
    pts[(cx - W + 1, top + 2)] = GOLD[3]; pts[(cx - W + 1, top + 3)] = GOLD[3]   # shine
    for (x, y) in list(pts):
        for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if q not in pts: c.p(*q, K)
    for q, col in pts.items(): c.p(*q, col)

def medal(c, cx, y0, rib):
    d, l = rib
    for i in range(6):                                  # V ribbon
        c.p(cx - 3 + i // 2, y0 + i, d); c.p(cx - 2 + i // 2, y0 + i, l)
        c.p(cx + 3 - i // 2, y0 + i, d); c.p(cx + 2 - i // 2, y0 + i, l)
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            if dx * dx + dy * dy <= 9:
                c.p(cx + dx, y0 + 9 + dy, K if dx * dx + dy * dy > 5 else GOLD[2])
    c.p(cx - 1, y0 + 8, GOLD[3]); c.p(cx + 1, y0 + 10, GOLD[1]); c.p(cx, y0 + 9, GOLD[0])

def nameplate(c, x0, x1, y):
    c.rect(x0, y, x1, y + 2, K); c.rect(x0 + 1, y + 1, x1 - 1, y + 1, GOLD[2]); c.p(x0 + 1, y + 1, GOLD[3])

def glass_cabinet(c, x0, y0, x1, y1):
    c.box(x0, y0, x1, y1, WOOD[1], WOOD[3], WOOD[0])
    c.rect(x0 - 1, y0 - 2, x1 + 1, y0, K); c.rect(x0, y0 - 1, x1, y0 - 1, WOOD[3])          # crown
    for (x, y) in ((x0 + 2, y0 - 4), (x1 - 2, y0 - 4), ((x0 + x1) // 2, y0 - 5)):            # gold finials
        c.rect(x - 1, y, x + 1, y + 2, K); c.p(x, y + 1, GOLD[2])
    gx0, gy0, gx1, gy1 = x0 + 4, y0 + 4, x1 - 4, y1 - 12
    c.rect(gx0 - 1, gy0 - 1, gx1 + 1, gy1 + 1, K)
    c.rect(gx0, gy0, gx1, gy1, GLASS[1])
    for y in range(gy0, gy1 + 1, 2):
        for x in range(gx0 + (y // 2) % 2, gx1 + 1, 4): c.p(x, y, GLASS[0])
    shelves = [gy0 + 30, gy0 + 60, gy0 + 90, gy1 - 12]
    for sy in shelves:
        c.rect(gx0, sy, gx1, sy + 1, WOOD[3]); c.rect(gx0, sy + 2, gx1, sy + 2, WOOD[0])
    mid = (gx0 + gx1) // 2
    cup(c, mid, shelves[0] - 1, 1.6)                                            # the grand cup
    cup(c, gx0 + 9, shelves[1] - 1, 0.9); cup(c, gx1 - 9, shelves[1] - 1, 0.9); medal(c, mid, shelves[0] + 8, RIBBONS[3])
    for i, rib in enumerate(RIBBONS[:3]): medal(c, gx0 + 9 + i * ((gx1 - gx0 - 18) // 2), shelves[1] + 8, rib)
    shield(c, mid, (shelves[2] + shelves[3]) // 2, 11)                           # crest between shelves 3 and 4
    n = (gx1 - gx0 - 4) // 10
    for i in range(n):                                                          # rolled scrolls on the bottom shelf
        sx = gx0 + 3 + i * 10
        c.rect(sx, shelves[3] - 4, sx + 8, shelves[3] - 1, K); c.rect(sx + 1, shelves[3] - 3, sx + 7, shelves[3] - 2, PARCH[2])
        c.p(sx + 1, shelves[3] - 3, PARCH[3]); c.p(sx + 4, shelves[3] - 3, SEAL[1]); c.p(sx + 4, shelves[3] - 2, SEAL[0])
    for i in range(3):                                                          # books under the scrolls
        bx = gx0 + 6 + i * 13
        for j, col in enumerate(((40, 70, 140), (120, 30, 44), (30, 100, 70))):
            c.rect(bx + j * 3, shelves[3] + 3, bx + j * 3 + 2, gy1, K); c.rect(bx + j * 3 + 1, shelves[3] + 4, bx + j * 3 + 1, gy1 - 1, col)
    # glass glints
    for (ox, oy, L) in ((gx0 + 2, gy0 + 3, 12), (gx0 + 5, gy0 + 3, 7), (gx1 - 9, gy1 - 30, 10)):   # glass glints
        for k in range(L):
            x, y = ox + k // 2, oy + k
            if gx0 <= x <= gx1 and gy0 <= y <= gy1 and c.px[x, y][:3] in GLASS: c.p(x, y, GLINT)
    # base drawer
    c.rect(x0 + 3, y1 - 10, x1 - 3, y1 - 3, WOOD[2]); c.rect(x0 + 3, y1 - 10, x1 - 3, y1 - 10, WOOD[4])
    c.rect(x0 + 3, y1 - 3, x1 - 3, y1 - 3, WOOD[0])
    c.rect((x0 + x1) // 2 - 2, y1 - 7, (x0 + x1) // 2 + 2, y1 - 6, GOLD[2])

def shield(c, cx, cy, r):
    for dx in range(-r - 1, r + 2):
        for dy in range(-r - 1, r + 2):
            d = dx * dx + dy * dy
            if d <= (r + 1) ** 2: c.p(cx + dx, cy + dy, K)
            if d <= r * r: c.p(cx + dx, cy + dy, SEAL[1] if (dx < 0) == (dy < 0) else (40, 70, 140))
            if r * r - 2 * r <= d <= r * r: c.p(cx + dx, cy + dy, GOLD[2] if dx + dy < 0 else GOLD[1])
    for k in range(-r + 2, r - 1): c.p(cx + k, cy, GOLD[2]); c.p(cx, cy + k, GOLD[2])
    c.rect(cx - 1, cy - 1, cx + 1, cy + 1, GOLD[3])
    for (x, y) in ((cx - r - 3, cy - r - 1), (cx + r + 3, cy - r - 1)):        # crossed swords behind
        pass

def pedestal(c, cx, by, h=16):
    x0, x1 = cx - 6, cx + 6
    c.box(x0, by - h, x1, by, (70, 78, 110), (110, 120, 156), (40, 46, 72))
    c.rect(x0 - 1, by - h - 2, x1 + 1, by - h, K); c.rect(x0, by - h - 1, x1, by - h - 1, (130, 140, 176))
    c.rect(x0 + 1, by - h + 4, x1 - 1, by - h + 4, GOLD[1])
    cup(c, cx, by - h - 3, 1.0)

def build():
    im = Image.open('tools/rooms_base/chronicle.png').convert('RGBA')
    c = Canvas(im)
    # left bay: certificate board (2 x 3)
    panel(c, 59, 44, 116, 143)
    for r in range(3):
        for col in range(2):
            certificate(c, 63 + col * 26, 49 + r * 31, 23, 28, f'cert{r}{col}')
    # centre bay: rebrick the strips the old tapestry leaves either side of the narrower cabinet
    # (copy from lower on the same columns, shifted by whole brick-pairs so the stagger lines up)
    src = im.copy().load()
    for x in list(range(150, 157)) + list(range(204, 209)):
        for y in range(44, 146 if x <= 206 else 51):              # x 207+ is the torch; only the rod end needs clearing
            sy = y + 14 * -(-(146 - y) // 14)
            c.px[x, y] = src[x, sy]
    # centre bay: glass trophy cabinet floor to top
    glass_cabinet(c, 156, 48, 204, 195)
    # right bay: course medals board (3 rows x 4) with nameplates
    panel(c, 243, 44, 300, 143)
    for r in range(3):
        for i in range(4):
            medal(c, 251 + i * 13, 50 + r * 31, RIBBONS[(r + i) % 4])
        nameplate(c, 248, 295, 66 + r * 31)
    # pedestal cups under the boards
    pedestal(c, 88, 195, 16); pedestal(c, 272, 195, 16)
    return im

if __name__ == '__main__':
    im = build()
    if sys.argv[1] == 'preview':
        im.resize((1440, 900), Image.NEAREST).save('sign-options/trophy-room.png')
    else:
        im.save('public/assets/rooms/trophy.png')
