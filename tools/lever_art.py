"""Gate lever + descending portcullis for the Gate Hall.
Usage: python3 tools/lever_art.py preview | write <A|B|C>"""
import sys, math
from PIL import Image

LW, LH = 17, 26          # lever canvas
LX, LY = 90, 150        # canvas top-left in room native px (next to the left torch)
PIV = (6, 13)            # pivot inside canvas

K = (8, 10, 24)
VAR = {
 # plate (dark, mid, light), handle (dark, light), knob (dark, mid, light)
 'A': dict(plate=((30, 32, 48), (66, 72, 98), (110, 118, 146)), handle=((60, 40, 26), (128, 86, 50)), knob=((74, 44, 24), (150, 98, 54), (204, 148, 92))),  # wooden grip
 'B': dict(plate=((70, 44, 18), (150, 104, 40), (224, 170, 76)), handle=((40, 42, 60), (120, 128, 156)), knob=((120, 80, 20), (224, 166, 64), (255, 230, 150))),
 'C': dict(plate=((34, 30, 46), (64, 58, 82), (100, 92, 120)), handle=((40, 42, 60), (120, 128, 156)), knob=((80, 40, 130), (170, 110, 240), (226, 196, 255)), rune=True),
}

def lever(v, up):
    P = VAR[v]; im = Image.new('RGBA', (LW, LH), (0, 0, 0, 0)); px = im.load()
    def put(x, y, c):
        if 0 <= x < LW and 0 <= y < LH: px[x, y] = c + (255,)
    # wall plate 7x13 with bevel + rivets + slot
    x0, y0, x1, y1 = 3, 6, 9, 20
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            edge = x in (x0, x1) or y in (y0, y1)
            c = K if edge else (P['plate'][2] if (x == x0 + 1 or y == y0 + 1) else P['plate'][0] if (x == x1 - 1 or y == y1 - 1) else P['plate'][1])
            put(x, y, c)
    for (x, y) in ((x0 + 1, y0 + 1), (x1 - 1, y0 + 1), (x0 + 1, y1 - 1), (x1 - 1, y1 - 1)): put(x, y, P['plate'][2])
    for y in range(y0 + 3, y1 - 2): put(PIV[0], y, K)                         # slot
    if P.get('rune'):
        for (x, y) in ((x0 + 2, y0 + 3), (x0 + 2, y1 - 3), (x1 - 2, y0 + 3), (x1 - 2, y1 - 3)): put(x, y, P['knob'][1])
    # handle: from pivot, angled up-right (open) or down-right (closed)
    L = 9
    pts = []
    for i in range(L + 1):
        p = (PIV[0] + round(i * 0.72), PIV[1] + (-1 if up else 1) * round(i * 0.72))
        if p not in pts: pts.append(p)
    thick = []
    for (x, y) in pts: thick += [(x, y), (x + 1, y)]          # 2px-wide shaft
    for (x, y) in thick:
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            q = (x + dx, y + dy)
            if q not in thick and 0 <= q[0] < LW and 0 <= q[1] < LH and px[q][3] == 0: put(*q, K)
    for (x, y) in pts: put(x, y, P['handle'][1]); put(x + 1, y, P['handle'][0])
    # knob 3x3 at the end
    kx, ky = pts[-1]
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            if abs(dx) == 2 and abs(dy) == 2: continue
            put(kx + dx, ky + dy, K)
    for dx in range(-1, 2):
        for dy in range(-1, 2): put(kx + dx, ky + dy, P['knob'][1])
    put(kx - 1, ky - 1, P['knob'][2]); put(kx + 1, ky + 1, P['knob'][0]); put(kx, ky + 1, P['knob'][0]); put(kx + 1, ky, P['knob'][0])
    # pivot bolt
    put(PIV[0], PIV[1], P['plate'][2]); 
    return im

# Portcullis: continues the baked grid below y=96 (verticals x=138+8k, horizontals every 8 from y=74)
PX0, PY0, PW, PH = 138, 74, 84, 122   # full gate: top of the arch slot to the floor
RAISED = 22                             # rows still visible in the arch when open
BAR, BAR_D, BAR_L = (58, 64, 88), (30, 34, 52), (96, 104, 136)
def portcullis():
    im = Image.new('RGBA', (PW, PH), (0, 0, 0, 0)); px = im.load()
    def put(x, y, c):
        if 0 <= x < PW and 0 <= y < PH and px[x, y][3] == 0 or (0 <= x < PW and 0 <= y < PH and c != BAR_D): px[x, y] = c + (255,)
    for k in range(0, PW, 8):
        for y in range(0, PH - 1):
            put(k, y, BAR)
        put(k, PH - 1, BAR_L)                                              # spike tip
    for y in range(4, PH - 10, 8):                                         # cross-bars; bottom 9 rows are bare spikes
        for x in range(0, PW - 3): put(x, y, BAR)
    # dark shadow pixel right/below each bar for readability over the sky
    for y in range(PH):
        for x in range(PW):
            if px[x, y][:3] == BAR:
                for q in ((x + 1, y), (x, y + 1)):
                    if q[0] < PW and q[1] < PH and px[q][3] == 0: px[q] = BAR_D + (255,)
    return im

def compose(v, up):
    room = Image.open('public/assets/rooms/gate.png').convert('RGBA')
    if not up: room.alpha_composite(portcullis(), (PX0, PY0))
    room.alpha_composite(lever(v, up), (LX, LY))
    return room

if __name__ == '__main__':
    if sys.argv[1] == 'preview':
        S = 4; box = (88, 60, 232, 200)
        rows = []
        for v in 'ABC':
            rows.append([compose(v, True).crop(box), compose(v, False).crop(box)])
        w, h = rows[0][0].size
        out = Image.new('RGBA', (2 * (w * S + 16), 3 * (h * S + 16)), (0, 0, 0, 255))
        for r, row in enumerate(rows):
            for c, t in enumerate(row): out.paste(t.resize((w * S, h * S), Image.NEAREST), (c * (w * S + 16), r * (h * S + 16)))
        out.save('sign-options/lever-lineup.png')
        z = []
        for v in 'ABC':
            for up in (True, False): z.append(lever(v, up))
        out = Image.new('RGBA', (6 * (LW * 12 + 12), LH * 12), (20, 24, 40, 255))
        for i, t in enumerate(z): out.alpha_composite(t.resize((LW * 12, LH * 12), Image.NEAREST), (i * (LW * 12 + 12), 0))
        out.save('sign-options/lever-zoom.png')
    else:
        v = sys.argv[2]
        lever(v, True).save('public/assets/sprites/lever_up.png')
        lever(v, False).save('public/assets/sprites/lever_down.png')
        portcullis().save('public/assets/sprites/portcullis.png')
