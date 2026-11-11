"""Embroider eldritch runes onto the red wall banners (a different inscription on every banner).
Usage: python3 tools/banner_runes.py preview | write <A|B|C>
Pristine rooms live in tools/rooms_base/. The gate room is finished by tools/sign_runes.py, which calls apply()."""
import sys, random
from PIL import Image

BANNERS = {'gate': [(85, 59), (275, 59)], 'treasury': [(180, 57)], 'armory': [(106, 48), (254, 48)], 'throne': [(148, 59), (212, 59)]}

GLYPHS = [
 ['###', '#.#', '###', '.#.'], ['#.#', '.#.', '.#.', '#.#'], ['##.', '..#', '.#.', '#..'], ['.#.', '###', '#.#', '#..'],
 ['#..', '###', '..#', '##.'], ['#.#', '###', '#.#', '.#.'], ['.##', '#..', '.#.', '##.'], ['###', '.#.', '#.#', '#.#'],
 ['#.#', '#.#', '.#.', '###'], ['..#', '.##', '#.#', '#..'], ['#..', '#.#', '###', '..#'], ['.#.', '#.#', '.#.', '#.#'],
 ['###', '#..', '##.', '#..'], ['#.#', '.##', '..#', '.##'], ['.#.', '.##', '#..', '###'], ['##.', '#.#', '##.', '#.#'],
]
STYLES = {
 'A': ((214, 150, 46), (58, 18, 28)),     # gold thread, dark stitch shadow
 'B': ((28, 10, 16), None),               # black ink
 'C': ((214, 168, 255), (58, 18, 28)),    # violet witch-thread (matches the signpost)
}

def gold(p): return p[0] > 150 and p[1] > 100 and p[2] < 90

def geometry(im, cx, cy):
    """emblem top/bottom and the gold stripes above and below it, scanning the banner's centre column."""
    px = im.load()
    et = cy
    while gold(px[cx, et - 1]) or not any(gold(px[cx + d, et - 1]) for d in (0,)) and any(gold(px[cx + d, et - 1]) for d in (-1, 1)): et -= 1
    eb = cy
    while any(gold(px[cx + d, eb + 1]) for d in (-1, 0, 1)): eb += 1
    # emblem may have a hollow centre: walk up/down through any gold in the 3 centre columns
    et = cy
    while any(gold(px[cx + d, et - 1]) for d in (-1, 0, 1)): et -= 1
    run = lambda y: sum(gold(px[x, y]) for x in range(cx - 6, cx + 7))
    st = et - 2
    while run(st) < 10: st -= 1
    sb = eb + 2
    while run(sb) < 10: sb += 1
    return et, eb, st, sb

def apply(im, room, style='A'):
    if room not in BANNERS: return im
    stroke, shadow = STYLES[style]
    px = im.load()
    for bi, (cx, cy) in enumerate(BANNERS[room]):
        et, eb, st, sb = geometry(im, cx, cy)
        rng = random.Random(f'{room}-{bi}')
        seq = rng.sample(range(len(GLYPHS)), len(GLYPHS))
        for (a, b) in ((st + 1, et - 1), (eb + 1, sb - 1)):       # free rows between stripe and emblem
            room_h = b - a + 1
            n = max(0, (room_h - 2 + 2) // 6)                       # 4-row glyph + 2-row gap
            if n == 0: continue
            used = n * 6 - 2
            y0 = a + (room_h - used) // 2
            for k in range(n):
                g = GLYPHS[seq.pop()]
                pts = [(cx - 1 + c, y0 + k * 6 + r) for r, row in enumerate(g) for c, ch in enumerate(row) if ch == '#']
                if shadow:
                    for (x, y) in pts:
                        q = (x + 1, y + 1)
                        if q not in pts: px[q] = shadow + (255,)
                for p in pts: px[p] = stroke + (255,)
    return im

def load(room): return Image.open(f'tools/rooms_base/{room}.png').convert('RGBA')

if __name__ == '__main__':
    if sys.argv[1] == 'preview':
        S = 4; tiles = []
        for st in ['orig', 'A', 'B', 'C']:
            row = []
            for room, bs in BANNERS.items():
                im = load(room) if st == 'orig' else apply(load(room), room, st)
                for (cx, cy) in bs: row.append(im.crop((cx - 13, cy - 32, cx + 13, cy + 42)))
            tiles.append(row)
        w, h = tiles[0][0].size
        out = Image.new('RGBA', (len(tiles[0]) * (w * S + 8), len(tiles) * (h * S + 12)), (0, 0, 0, 255))
        for r, row in enumerate(tiles):
            for c, t in enumerate(row): out.paste(t.resize((w * S, h * S), Image.NEAREST), (c * (w * S + 8), r * (h * S + 12)))
        out.save('sign-options/banners.png')
    else:
        st = sys.argv[2]
        for room in BANNERS:
            if room == 'gate': continue                      # gate is assembled by sign_runes.py
            apply(load(room), room, st).save(f'public/assets/rooms/{room}.png')
