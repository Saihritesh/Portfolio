"""Move the rune signpost from the Gate Hall to the Chronicle Hall (the first room of the tour).
Usage: python3 tools/signpost_move.py preview | write
Reads the finished gate.png from tools/sign_runes.py (via build_gate) and tools/rooms_base/chronicle.png."""
import sys
sys.path.insert(0, 'tools')
from PIL import Image
import sign_runes

BOX = (244, 152, 283, 196)     # signpost bounds in the gate room (x0, y0, x1, y1 exclusive)
DX = 70 - 263                  # post moves from x=263 (gate) to x=70 (chronicle, by the entrance door)
SIGN_STYLE = 'A'              # burnt-in runes (see tools/sign_runes.py VARIANTS)

def gate_with_sign():
    return sign_runes.apply(sign_runes.base(), SIGN_STYLE)

def is_sign(p):
    """the signpost is wood/runes (warm or violet); the wall behind it is cool blue"""
    r, g, b = p[:3]
    return r > b or (r > 150 and b > 200)

def sign_mask(im):
    px = im.load()
    return {(x, y) for x in range(BOX[0], BOX[2]) for y in range(BOX[1], BOX[3]) if is_sign(px[x, y])}

def remove_sign(im):
    """replace each signpost pixel with the nearest wall pixel a whole brick-pair (14 px) above it"""
    mask = sign_mask(im); src = im.copy().load(); px = im.load()
    for (x, y) in mask:
        sy = y - 14
        while (x, sy) in mask: sy -= 14
        px[x, y] = src[x, sy]
    return im

def sign_sprite():
    a = gate_with_sign(); pa = a.load()
    out = Image.new('RGBA', (BOX[2] - BOX[0], BOX[3] - BOX[1]), (0, 0, 0, 0)); po = out.load()
    for (x, y) in sign_mask(a): po[x - BOX[0], y - BOX[1]] = pa[x, y]
    return out

def chronicle_with_sign():
    im = Image.open('tools/rooms_base/chronicle.png').convert('RGBA')
    im.alpha_composite(sign_sprite(), (BOX[0] + DX, BOX[1]))
    return im

if __name__ == '__main__':
    gate = remove_sign(gate_with_sign()); chron = chronicle_with_sign()
    if sys.argv[1] == 'preview':
        S = 2
        out = Image.new('RGBA', (360 * S, 225 * S * 2 + 12), (0, 0, 0, 255))
        out.paste(chron.resize((360 * S, 225 * S), Image.NEAREST), (0, 0))
        out.paste(gate.resize((360 * S, 225 * S), Image.NEAREST), (0, 225 * S + 12))
        out.save('sign-options/signpost-move.png')
        z = Image.new('RGBA', (2 * 120 * 4 + 12, 70 * 4), (0, 0, 0, 255))
        z.paste(chron.crop((30, 130, 150, 200)).resize((480, 280), Image.NEAREST), (0, 0))
        z.paste(gate.crop((220, 130, 340, 200)).resize((480, 280), Image.NEAREST), (492, 0))
        z.save('sign-options/signpost-move-zoom.png')
    else:
        gate.save('public/assets/rooms/gate.png'); chron.save('public/assets/rooms/chronicle.png')
