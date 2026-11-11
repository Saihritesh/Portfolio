"""Carve eldritch runes into the Gate Hall signpost boards.
Usage: python3 tools/sign_runes.py preview | write <A|B|C>
Reads tools/gate_base.png (pristine room), writes public/assets/rooms/gate.png."""
import sys
from PIL import Image

# 3x4 eldritch glyphs ('#' = stroke)
G = {
 'eye':  ['###', '#.#', '###', '.#.'],
 'fork': ['#.#', '.#.', '.#.', '#.#'],
 'hook': ['##.', '..#', '.#.', '#..'],
 'tri':  ['.#.', '###', '#.#', '#..'],
 'spin': ['#..', '###', '..#', '##.'],
 'bar':  ['#.#', '###', '#.#', '.#.'],
}
BOARDS = [((266, 160), ['eye', 'hook', 'fork']),   # right board, interior x265..278
          ((250, 172), ['tri', 'spin', 'bar'])]    # left board, interior x248..261

VARIANTS = {
 # name: (stroke, glow or None)
 'A': ((52, 28, 16), None),                       # carved, burnt-in
 'B': ((150, 255, 190), (60, 36, 22)),           # sickly green witchlight
 'C': ((214, 168, 255), (60, 36, 22)),          # violet void glow
}

GROOVE = ((0, 1),)  # single-pixel carved groove under each stroke
# each board grows one pixel taller at the bottom: (x0, x1, y) rows painted with wood
EXTEND = [(265, 278, 165), (248, 261, 177)]

def apply(im, v):
    stroke, glow = VARIANTS[v]
    px = im.load()
    for x0, x1, y in EXTEND:
        for x in range(x0, x1 + 1): px[x, y] = (110, 70, 40, 255)
    pts = set()
    for (ox, oy), word in BOARDS:
        for i, g in enumerate(word):
            for r, row in enumerate(G[g]):
                for c, ch in enumerate(row):
                    if ch == '#': pts.add((ox + i * 4 + c, oy + r))
    if glow:  # carved groove: the wood just below/right of each stroke is burnt dark
        for (x, y) in pts:
            for q in GROOVE:
                q = (x + q[0], y + q[1])
                if q not in pts and px[q][:3] == (110, 70, 40): px[q] = glow + (255,)
    for p in pts: px[p] = stroke + (255,)
    return im

BAR = (58, 64, 88)
def strip_bars(im):
    """Remove the raised portcullis baked into the room; it's now a separate sprite (tools/lever_art.py)."""
    px = im.load()
    isbar = lambda x, y: px[x, y][:3] == BAR
    cols = range(138, 223, 8)
    for x in cols:                                   # spike tips under the bottom row
        if px[x, 96][:3] in ((106, 114, 144), (123, 124, 146)): px[x, 96] = px[x, 97]
    src = im.copy().load()
    bar = lambda x, y: src[x, y][:3] == BAR
    for y in range(70, 97):
        for x in range(134, 226):
            if not bar(x, y): continue
            horiz = bar(x - 1, y) or bar(x + 1, y)
            order = ((x, y - 1), (x, y + 1), (x + 1, y - 1), (x - 1, y + 1)) if horiz else ((x + 1, y), (x - 1, y), (x + 1, y - 1))
            for q in order + ((x, y - 2), (x, y + 2), (x + 2, y)):
                if not bar(*q): px[x, y] = src[q]; break
    return im

GATE_VISTA = 'forest'   # the view out through the arch, see tools/gate_vista.py
BANNER_STYLE = 'C'   # violet witch-thread, see tools/banner_runes.py

def base():
    sys.path.insert(0, "tools"); from banner_runes import apply as banners
    import gate_vista
    im = gate_vista.apply(strip_bars(Image.open('tools/gate_base.png').convert('RGBA')), GATE_VISTA)
    return banners(im, 'gate', BANNER_STYLE)

if __name__ == '__main__':
    if sys.argv[1] == 'preview':
        S = 4; box = (225, 135, 305, 200)
        tiles = [base().crop(box)] + [apply(base(), v).crop(box) for v in 'ABC']
        w, h = tiles[0].size
        out = Image.new('RGBA', ((w * S + 16) * 4, h * S), (0, 0, 0, 255))
        for i, t in enumerate(tiles): out.paste(t.resize((w * S, h * S), Image.NEAREST), (i * (w * S + 16), 0))
        out.save('sign-options/lineup.png')
    else:
        apply(base(), sys.argv[2]).save('public/assets/rooms/gate.png')
