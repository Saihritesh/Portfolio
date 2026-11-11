"""Treasury: clear all eight pedestals, then stand five of them back up, centred in the room.
Usage: python3 tools/treasury_art.py preview | write
Starts from tools/rooms_base/treasury.png and re-applies the banner runes (tools/banner_runes.py)."""
import sys
sys.path.insert(0, 'tools')
from PIL import Image
import banner_runes

ALL = [(x0 - 2, x1 + 2) for x0, x1 in [(63, 81), (94, 112), (125, 143), (156, 174), (189, 207), (218, 238), (249, 269), (280, 300)]]   # x-spans incl. cap outlines
REMOVE = ALL
CENTRES = [118, 149, 180, 211, 242]      # five pedestals, 31 px apart, centred on the room's middle (x=180)
PROTO = (92, 114)                        # pedestal 2 is the template (outside the window light)
Y0, Y1 = 167, 195

def in_pedestal(x, y):
    return Y0 <= y <= Y1 and any(x0 <= x <= x1 for x0, x1 in ALL)

def paint_out(im):
    """refill from the wall up-and-left along the window's light beam (slope ~1),
    stepping a whole brick (13 px) across and a brick-pair (14 px) up so the pattern stays aligned"""
    src = im.copy().load(); px = im.load()
    for x0, x1 in REMOVE:
        for x in range(x0, x1 + 1):
            for y in range(Y0, Y1 + 1):
                sx, sy = x - 13, y - 14
                while in_pedestal(sx, sy): sx -= 13; sy -= 14
                px[x, y] = src[sx, sy]
    return im

def pedestal_sprite(orig, cleared):
    """the template pedestal: pixels that differ from the cleared wall"""
    po, pc = orig.load(), cleared.load()
    x0, x1 = PROTO
    out = Image.new('RGBA', (x1 - x0 + 1, Y1 - Y0 + 1), (0, 0, 0, 0)); pq = out.load()
    for x in range(x0, x1 + 1):
        for y in range(Y0, Y1 + 1):
            if po[x, y] != pc[x, y]: pq[x - x0, y - Y0] = po[x, y]
    return out

def build():
    orig = Image.open('tools/rooms_base/treasury.png').convert('RGBA')
    im = paint_out(orig.copy())
    spr = pedestal_sprite(orig, im)
    half = (PROTO[1] - PROTO[0]) // 2
    for cx in CENTRES: im.alpha_composite(spr, (cx - half, Y0))
    return banner_runes.apply(im, 'treasury', 'C')

if __name__ == '__main__':
    after = build()
    if sys.argv[1] == 'preview':
        before = Image.open('public/assets/rooms/treasury.png').convert('RGBA')
        box = (150, 100, 330, 205); w, h = box[2] - box[0], box[3] - box[1]
        out = Image.new('RGBA', (w * 4, h * 8 + 12), (0, 0, 0, 255))
        out.paste(before.crop(box).resize((w * 4, h * 4), Image.NEAREST), (0, 0))
        out.paste(after.crop(box).resize((w * 4, h * 4), Image.NEAREST), (0, h * 4 + 12))
        out.save('sign-options/treasury-pedestals.png')
        after.resize((1440, 900), Image.NEAREST).save('sign-options/treasury-full.png')
    else:
        after.save('public/assets/rooms/treasury.png')
