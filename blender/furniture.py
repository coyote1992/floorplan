"""Furniture builders. Each returns a Geo in local coordinates:
origin = centre of the footprint on the floor, +Z up, the FRONT of the piece faces -Y, width along X.
Dimensions follow the real pieces seen in the photos (mostly IKEA catalogue sizes)."""
import bmesh
from math import pi, sin, cos, radians
from mathutils import Vector
from lib import (Geo, box, box_ext, cyl, lathe, sweep, tube, prism, rect2d, circle2d, smooth_path,
                 grid_surface, xform, boolean, open_box, rng)

M = {}   # material dictionary, filled by build.py


def rbox(sx, sy, sz, at=(0, 0, 0), r=0.03, seg=4, origin='bottom'):
    return box(sx, sy, sz, at=at, bevel=r, seg=seg, origin=origin)


# ============================================================ living room
def sofa_friheten():
    """IKEA FRIHETEN corner sofa-bed, 230 x 151 x 66 cm, chaise on the left (-X)."""
    g = Geo()
    f, fd = M['fab_sofa'], M['fab_sofa']
    g.add(box_ext(-1.15, -0.44, 0.05, 1.15, 0.44, 0.31, bevel=0.02), f)               # main base
    g.add(box_ext(-1.15, -1.07, 0.05, -0.27, -0.40, 0.31, bevel=0.02), f)             # chaise base
    for x, y in ((-1.10, -1.02), (1.10, -0.39), (-1.10, 0.39), (1.10, 0.39), (-0.32, -1.02)):
        g.add(cyl(0.022, 0.05, at=(x, y, 0), seg=12), M['metal_black'])
    g.add(box_ext(-1.15, 0.20, 0.31, 1.15, 0.44, 0.60, bevel=0.05, seg=5), fd)        # back frame
    g.add(box_ext(0.96, -0.44, 0.31, 1.15, 0.24, 0.58, bevel=0.05, seg=5), fd)        # right arm
    g.add(box_ext(-1.15, -1.07, 0.31, -0.98, 0.24, 0.50, bevel=0.05, seg=5), fd)      # chaise side
    g.add(box_ext(-0.27, -0.44, 0.31, 0.96, 0.21, 0.46, bevel=0.055, seg=5), f)       # main seat cushion
    g.add(box_ext(-0.98, -1.07, 0.31, -0.27, 0.21, 0.46, bevel=0.055, seg=5), f)      # chaise cushion
    w = (0.96 + 0.98) / 3
    for i in range(3):
        x = -0.98 + w * (i + 0.5)
        g.add(rbox(w - 0.02, 0.19, 0.30, r=0.06, seg=5, origin='center'), f, rx=-0.20, loc=(x, 0.10, 0.60))
    # throw pillows
    g.add(rbox(0.44, 0.13, 0.42, r=0.06, seg=5, origin='center'), M['fab_linen'], rx=-0.30, rz=0.15, loc=(-0.66, -0.06, 0.66))
    g.add(rbox(0.42, 0.12, 0.40, r=0.06, seg=5, origin='center'), M['fab_grey'], rx=-0.30, rz=-0.1, loc=(0.62, -0.04, 0.65))
    return g


def lack_table():
    """IKEA LACK coffee table 90 x 55 x 45, white stained oak effect."""
    g = Geo()
    m = M['wood_lack']
    g.add(box_ext(-0.45, -0.275, 0.40, 0.45, 0.275, 0.45, bevel=0.003), m, grain=0)
    for sx in (-1, 1):
        for sy in (-1, 1):
            g.add(box(0.05, 0.05, 0.40, at=(sx * 0.425, sy * 0.25, 0), bevel=0.002), m, grain=2)
    g.add(box_ext(-0.40, -0.25, 0.12, 0.40, 0.25, 0.14, bevel=0.002), m, grain=0)
    # a tidy tray with a candle
    g.add(box(0.30, 0.20, 0.012, at=(0.12, 0.0, 0.45), bevel=0.004), M['wood_oak'])
    g.add(lathe([(0.0, 0.462), (0.045, 0.462), (0.045, 0.55), (0.0, 0.55)], seg=24), M['ceramic_white'], loc=(0.05, 0.0, 0))
    return g


def not_lamp(mat_body='metal_black'):
    """IKEA NOT floor uplighter with reading arm, 176 cm."""
    g = Geo()
    b = M[mat_body]
    g.add(cyl(0.13, 0.018, seg=40, bevel=0.006), b)
    g.add(cyl(0.012, 1.62, at=(0, 0, 0.018), seg=12), b)
    g.add(lathe([(0.030, 1.60), (0.048, 1.62), (0.165, 1.76), (0.160, 1.762), (0.044, 1.625), (0.0, 1.625)], seg=40), M['plastic_white'])
    arm = [(0, 0, 1.10), (0.06, 0, 1.25), (0.16, 0, 1.33), (0.24, 0, 1.33)]
    g.add(tube(arm, 0.008, n=10, sub=6), b)
    g.add(lathe([(0.018, 0.0), (0.06, -0.10), (0.058, -0.102), (0.0, -0.02)], seg=28), M['plastic_white'], ry=0.6, loc=(0.25, 0, 1.36))
    return g


def poang():
    """IKEA POÄNG armchair 68 x 82 x 100, birch veneer, grey cushion."""
    g = Geo()
    wood = M['wood_birch']
    loop = [(-0.36, 0.02), (-0.385, 0.20), (-0.36, 0.42), (-0.29, 0.55), (-0.15, 0.585), (0.10, 0.585),
            (0.24, 0.52), (0.33, 0.33), (0.35, 0.12), (0.30, 0.02), (0.0, 0.015)]
    pts = smooth_path([(0, y, z) for y, z in loop] + [(0, -0.36, 0.02)], 6)
    for sx in (-0.31, 0.31):
        g.add(sweep([p + Vector((sx, 0, 0)) for p in pts[:-1]], rect2d(0.026, 0.05, 0.008, 2), normal_hint=(1, 0, 0),
                    closed_path=True, caps=False), wood, grain=1)
    seat = [(-0.33, 0.43), (-0.25, 0.405), (-0.08, 0.35), (0.10, 0.36), (0.22, 0.47), (0.29, 0.70), (0.33, 0.99)]
    sp = smooth_path([(0, y, z) for y, z in seat], 8)
    g.add(sweep(sp, rect2d(0.56, 0.012), normal_hint=(1, 0, 0)), wood, grain=1)
    off = []
    for i, p in enumerate(sp):
        t = (sp[min(i + 1, len(sp) - 1)] - sp[max(i - 1, 0)]).normalized()
        n = Vector((0, -t.z, t.y))
        off.append(p + n * 0.045)
    g.add(sweep(off, rect2d(0.55, 0.075, 0.03, 3), normal_hint=(1, 0, 0)), M['fab_charcoal'])
    for y, z in ((-0.30, 0.40), (0.27, 0.50), (0.30, 0.12)):
        g.add(cyl(0.014, 0.62, at=(-0.31, y, z), seg=12, axis='X'), wood)
    return g


def billy(books=True):
    """IKEA BILLY bookcase 80 x 28 x 202, black-brown."""
    g = Geo()
    m = M['wood_billy']
    g.add(box_ext(-0.40, -0.14, 0, -0.382, 0.14, 2.02, bevel=0.002), m, grain=2)
    g.add(box_ext(0.382, -0.14, 0, 0.40, 0.14, 2.02, bevel=0.002), m, grain=2)
    g.add(box_ext(-0.382, -0.14, 2.0, 0.382, 0.14, 2.02, bevel=0.002), m, grain=0)
    g.add(box_ext(-0.382, -0.12, 0, 0.382, -0.10, 0.06), m, grain=0)
    g.add(box_ext(-0.40, 0.132, 0, 0.40, 0.14, 2.02), m, grain=2)
    shelves = [0.06, 0.40, 0.73, 1.06, 1.39, 1.70]
    for z in shelves:
        g.add(box_ext(-0.382, -0.13, z, 0.382, 0.13, z + 0.018, bevel=0.0015), m, grain=0)
    if books:
        pal = [M[k] for k in ('book_a', 'book_b', 'book_c', 'book_d', 'book_e', 'book_f')]
        for si, z in enumerate(shelves[1:5]):
            x = -0.37
            limit = 0.37 - (0.12 if si % 2 else 0.0)
            while x < limit:
                bw = rng.uniform(0.022, 0.045)
                bh = rng.uniform(0.19, 0.27)
                bd = rng.uniform(0.15, 0.21)
                if x + bw > limit:
                    break
                g.add(box(bw, bd, bh, at=(x + bw / 2, -0.12 + bd / 2 + 0.02, z + 0.018), bevel=0.002), rng.choice(pal))
                x += bw + 0.002
            if si % 2:
                g.add(lathe([(0.0, 0.0), (0.035, 0.0), (0.05, 0.08), (0.03, 0.16), (0.032, 0.17), (0.0, 0.17)], seg=24),
                      M['ceramic_white'], loc=(0.31, 0.0, z + 0.018))
    return g


def dark_cabinet():
    g = Geo()
    m = M['wood_dark']
    g.add(box_ext(-0.225, -0.175, 0.04, 0.225, 0.175, 0.95, bevel=0.004), m, grain=2)
    for i in range(3):
        z0 = 0.10 + i * 0.28
        g.add(box_ext(-0.205, -0.182, z0, 0.205, -0.175, z0 + 0.26, bevel=0.003), m, grain=0)
        g.add(cyl(0.012, 0.02, at=(0, -0.185, z0 + 0.13), seg=12, axis='Y'), M['brass'])
    for sx in (-0.2, 0.2):
        for sy in (-0.15, 0.15):
            g.add(box(0.035, 0.035, 0.04, at=(sx, sy, 0)), m)
    return g


def cube_shelf():
    """Low 3x3 cube shelf 112 x 39 x 112, white, cubbies at the front (-Y)."""
    g = Geo()
    m = M['white_furn']
    W, D, Hh, t, ti = 1.12, 0.39, 1.12, 0.038, 0.016
    g.add(box_ext(-W / 2, -D / 2, 0, -W / 2 + t, D / 2, Hh, bevel=0.002), m)
    g.add(box_ext(W / 2 - t, -D / 2, 0, W / 2, D / 2, Hh, bevel=0.002), m)
    g.add(box_ext(-W / 2 + t, -D / 2, Hh - t, W / 2 - t, D / 2, Hh, bevel=0.002), m)
    g.add(box_ext(-W / 2 + t, -D / 2, 0, W / 2 - t, D / 2, t, bevel=0.002), m)
    g.add(box_ext(-W / 2, D / 2 - 0.004, 0, W / 2, D / 2, Hh), m)
    cw = (W - 2 * t - 2 * ti) / 3
    for i in (1, 2):
        x = -W / 2 + t + i * cw + (i - 0.5) * ti
        g.add(box_ext(x - ti / 2, -D / 2, t, x + ti / 2, D / 2, Hh - t), m)
        z = t + i * cw + (i - 0.5) * ti
        g.add(box_ext(-W / 2 + t, -D / 2, z - ti / 2, W / 2 - t, D / 2, z + ti / 2), m)
    # contents: two baskets, some books
    cx = [-W / 2 + t + cw * (i + 0.5) + i * ti for i in range(3)]
    cz = [t + cw * j + j * ti for j in range(3)]
    for (i, j) in ((0, 0), (2, 1)):
        g.add(rbox(cw * 0.85, 0.30, cw * 0.72, at=(cx[i], -0.02, cz[j]), r=0.01, seg=2), M['rattan'])
    for (i, j) in ((1, 0), (0, 2), (1, 1)):
        x = cx[i] - cw / 2 + 0.03
        while x < cx[i] + cw / 2 - 0.08:
            bw = rng.uniform(0.02, 0.04)
            bh = rng.uniform(0.2, 0.28)
            g.add(box(bw, 0.2, bh, at=(x + bw / 2, 0.02, cz[j]), bevel=0.002),
                  M[rng.choice(('book_a', 'book_b', 'book_c', 'book_d', 'book_e', 'book_f'))])
            x += bw + 0.003
    g.add(box(0.16, 0.02, 0.21, at=(-0.30, 0.05, Hh), bevel=0.004), M['wood_oak'], rx=0.12)
    return g


def dining_table(d=1.05):
    g = Geo()
    g.add(cyl(d / 2, 0.03, at=(0, 0, 0.72), seg=72, bevel=0.006, bseg=3), M['wood_oak'])
    g.add(cyl(0.13, 0.03, at=(0, 0, 0.69), seg=32), M['metal_black'])
    for k in range(4):
        a = pi / 4 + k * pi / 2
        p0 = Vector((cos(a) * 0.08, sin(a) * 0.08, 0.70))
        p1 = Vector((cos(a) * 0.42, sin(a) * 0.42, 0.0))
        g.add(sweep([p0, p1], rect2d(0.035, 0.035, 0.004, 1)), M['metal_black'])
    return g


def sled_chair():
    """Upholstered velvet sled chair with chrome frame and oak arm rests."""
    g = Geo()
    v = M['fab_velvet']
    g.add(rbox(0.46, 0.46, 0.09, at=(0, -0.02, 0.40), r=0.035, seg=4), v)
    g.add(rbox(0.46, 0.08, 0.40, r=0.035, seg=4, origin='center'), v, rx=-0.16, loc=(0, 0.21, 0.70))
    loop = [(-0.24, 0.012), (-0.25, 0.62), (0.16, 0.64), (0.24, 0.012)]
    for sx in (-0.255, 0.255):
        pts = [Vector((sx, y, z)) for y, z in loop]
        path = smooth_path(pts + [pts[0]], 1)
        g.add(sweep(pts + [pts[0]], circle2d(0.011, 12), closed_path=False), M['chrome'])
        g.add(box(0.05, 0.42, 0.025, at=(sx, -0.04, 0.635), bevel=0.008), M['wood_oak'])
    g.add(cyl(0.01, 0.50, at=(-0.25, 0.14, 0.38), seg=10, axis='X'), M['chrome'])
    return g


def folding_chair():
    g = Geo()
    b = M['metal_black']
    for sx in (-0.2, 0.2):
        g.add(sweep([(sx, 0.20, 0), (sx, 0.16, 0.86)], circle2d(0.011, 10)), b)
        g.add(sweep([(sx, -0.22, 0), (sx, 0.12, 0.45)], circle2d(0.011, 10)), b)
    g.add(rbox(0.42, 0.40, 0.05, at=(0, -0.02, 0.44), r=0.02, seg=3), M['fab_charcoal'])
    g.add(rbox(0.40, 0.03, 0.20, at=(0, 0.17, 0.62), r=0.012, seg=3), M['fab_charcoal'])
    return g


def drum_pendant(drop, r=0.24, h=0.24):
    """Fabric drum shade hanging `drop` m below the ceiling (origin at the ceiling)."""
    g = Geo()
    z1 = -drop
    g.add(cyl(0.05, 0.02, at=(0, 0, -0.02), seg=24), M['plastic_white'])
    g.add(cyl(0.004, drop - h, at=(0, 0, z1 + h), seg=6), M['metal_black'])
    g.add(lathe([(r, z1), (r, z1 + h)], seg=64), M['fab_shade'])
    g.add(lathe([(r - 0.003, z1 + h), (r - 0.003, z1)], seg=64), M['shade_glow'])
    g.add(lathe([(0.0, z1 + 0.05), (0.03, z1 + 0.06), (0.03, z1 + 0.11), (0.0, z1 + 0.12)], seg=16), M['bulb'])
    return g


def lantern(drop, r=0.225):
    """IKEA REGOLIT paper lantern."""
    g = Geo()
    prof = []
    for i in range(1, 40):
        ph = pi * i / 40
        rr = r * sin(ph) * (1 + 0.012 * sin(ph * 30))
        prof.append((rr, -drop + r - r * cos(ph)))
    prof = [(0.03, -drop)] + [p for p in prof if p[0] > 0.03] + [(0.04, -drop + 2 * r)]
    g.add(lathe(prof, seg=48), M['paper_glow'])
    g.add(cyl(0.004, drop - 2 * r, at=(0, 0, -drop + 2 * r), seg=6), M['plastic_white'])
    g.add(cyl(0.04, 0.02, at=(0, 0, -0.02), seg=24), M['plastic_white'])
    return g


def poster_frame():
    """Vintage poster 50 x 70 cm with wooden hanger rails. Front faces -Y."""
    g = Geo()
    g.add(box(0.50, 0.004, 0.70, at=(0, 0, 0)), M['poster'])
    for z in (-0.005, 0.69):
        g.add(box(0.54, 0.018, 0.016, at=(0, -0.006, z), bevel=0.003), M['wood_oak'])
    g.add(sweep([(-0.22, -0.003, 0.705), (0, 0.0, 0.86), (0.22, -0.003, 0.705)], circle2d(0.0015, 6)), M['metal_black'])
    return g


def ac_unit():
    g = Geo()
    g.add(rbox(0.80, 0.21, 0.28, r=0.03, seg=4), M['plastic_gloss'])
    g.add(box(0.70, 0.01, 0.025, at=(0, -0.105, 0.02)), M['plastic_dark'])
    g.add(box(0.12, 0.004, 0.02, at=(0.28, -0.107, 0.21)), M['plastic_dark'])
    return g


def radiator(w, h=0.55, d=0.10):
    """Steel panel radiator with vertical channels; origin bottom centre, sits on brackets."""
    g = Geo()
    r = M['radiator']
    g.add(box(w, d, h, at=(0, 0, 0), bevel=0.006), r)
    n = int(w / 0.033)
    for i in range(n):
        x = -w / 2 + (i + 0.5) * w / n
        g.add(box(0.016, 0.006, h - 0.06, at=(x, -d / 2 - 0.002, 0.03), bevel=0.003), r)
    g.add(cyl(0.012, 0.06, at=(w / 2 + 0.03, 0, 0.02), seg=12), M['chrome'])
    return g


def curtain(width, height, folds=7, amp=0.035, matname='sheer'):
    g = Geo()

    def f(u, v):
        x = (u - 0.5) * width
        return (x, amp * sin(u * folds * 2 * pi), v * height)
    g.add(grid_surface(f, folds * 8, 2), M[matname])
    return g


def curtain_rod(length):
    g = Geo()
    g.add(cyl(0.01, length, at=(-length / 2, 0, 0), seg=12, axis='X'), M['metal_black'])
    for x in (-length / 2, length / 2):
        g.add(lathe([(0.0, -0.015), (0.016, -0.012), (0.016, 0.012), (0.0, 0.015)], seg=16), M['metal_black'], ry=pi / 2, loc=(x, 0, 0))
    return g


def rug(w, d, matname):
    g = Geo()
    g.add(box(w, d, 0.008, bevel=0.003, seg=1), M[matname])
    return g


# ============================================================ bedroom
def daybed_hemnes():
    """IKEA HEMNES day-bed, extended to double (208 x 168). Length along X, backrest on +Y."""
    g = Geo()
    w = M['white_furn']
    L = 2.08
    for x in (-1.02, 1.02):
        for y in (0.82, 0.0):
            g.add(box(0.05, 0.05, 0.86 if y > 0.5 else 0.70, at=(x, y, 0), bevel=0.006), w)
        g.add(box(0.04, 0.84, 0.05, at=(x, 0.41, 0.65), bevel=0.006), w)
        g.add(box(0.04, 0.84, 0.08, at=(x, 0.41, 0.20), bevel=0.004), w)
        for k in range(7):
            g.add(box(0.025, 0.035, 0.37, at=(x, 0.06 + k * 0.11, 0.28)), w)
    g.add(box(L, 0.05, 0.06, at=(0, 0.82, 0.80), bevel=0.008), w)
    g.add(box(L, 0.04, 0.10, at=(0, 0.82, 0.18), bevel=0.005), w)
    for k in range(17):
        g.add(box(0.035, 0.025, 0.52, at=(-0.96 + k * 0.12, 0.82, 0.28)), w)
    g.add(box(2.0, 0.84, 0.16, at=(0, 0.40, 0.10), bevel=0.004), w)
    g.add(box(2.0, 0.80, 0.14, at=(0, -0.42, 0.10), bevel=0.004), w)
    g.add(box(2.0, 0.03, 0.14, at=(0, -0.82, 0.10), bevel=0.004), w)
    # mattresses + bedding
    g.add(rbox(1.98, 1.60, 0.17, at=(0, 0.0, 0.25), r=0.04, seg=4), M['fab_white'])
    g.add(rbox(1.42, 1.66, 0.075, at=(0.29, -0.01, 0.40), r=0.035, seg=5), M['fab_linen'])     # duvet
    g.add(rbox(0.40, 1.66, 0.04, at=(0.80, -0.01, 0.465), r=0.015, seg=3), M['fab_linen'])    # throw at foot
    for y in (-0.38, 0.38):
        g.add(rbox(0.46, 0.66, 0.13, at=(-0.73, y, 0.41), r=0.05, seg=5), M['fab_white'])
    g.add(rbox(0.42, 0.12, 0.40, r=0.06, seg=5, origin='center'), M['fab_linen'], rx=-0.25, loc=(-0.2, 0.68, 0.62))
    return g


def desk():
    g = Geo()
    g.add(box(1.20, 0.60, 0.025, at=(0, 0, 0.715), bevel=0.003), M['wood_birch'], grain=0)
    for sx in (-0.56, 0.56):
        for sy in (-0.26, 0.26):
            g.add(box(0.04, 0.04, 0.715, at=(sx, sy, 0), bevel=0.003), M['metal_grey'])
        g.add(box(0.03, 0.50, 0.04, at=(sx, 0, 0.67)), M['metal_grey'])
    # monitor, keyboard, mouse
    g.add(box(0.22, 0.17, 0.012, at=(-0.15, 0.12, 0.74), bevel=0.004), M['plastic_dark'])
    g.add(box(0.04, 0.025, 0.24, at=(-0.15, 0.17, 0.74)), M['plastic_dark'])
    g.add(box(0.54, 0.025, 0.33, at=(-0.15, 0.15, 0.90), bevel=0.004), M['plastic_dark'])
    g.add(box(0.51, 0.004, 0.29, at=(-0.15, 0.136, 0.92)), M['screen'])
    g.add(box(0.43, 0.14, 0.018, at=(-0.15, -0.12, 0.74), bevel=0.004), M['plastic_dark'])
    g.add(rbox(0.06, 0.10, 0.03, at=(0.20, -0.12, 0.74), r=0.014, seg=3), M['plastic_dark'])
    return g


def slat_chair():
    g = Geo()
    b = M['wood_black']
    for sx in (-0.19, 0.19):
        g.add(box(0.035, 0.035, 0.44, at=(sx, -0.18, 0), bevel=0.003), b)
        g.add(box(0.035, 0.035, 0.86, at=(sx, 0.19, 0), bevel=0.003), b, rx=-0.08)
    g.add(box(0.44, 0.42, 0.025, at=(0, 0.0, 0.44), bevel=0.004), b)
    for z in (0.62, 0.72, 0.82):
        g.add(box(0.38, 0.018, 0.06, at=(0, 0.22 + (z - 0.44) * 0.08, z), bevel=0.003), b)
    return g


def drawers(w, d, h, n, mat='wood_pine', knob='wood_pine', plinth=0.05, top_mat=None):
    """Chest of drawers (TARVA style)."""
    g = Geo()
    m = M[mat]
    t = 0.02
    g.add(box_ext(-w / 2, -d / 2 + 0.01, 0, -w / 2 + t, d / 2, h - 0.02, bevel=0.002), m, grain=2)
    g.add(box_ext(w / 2 - t, -d / 2 + 0.01, 0, w / 2, d / 2, h - 0.02, bevel=0.002), m, grain=2)
    g.add(box_ext(-w / 2 - 0.01, -d / 2, h - 0.025, w / 2 + 0.01, d / 2, h, bevel=0.003), M[top_mat or mat], grain=0)
    g.add(box_ext(-w / 2 + t, -d / 2 + 0.03, 0, w / 2 - t, d / 2, plinth), m)
    dh = (h - 0.025 - plinth - 0.004 * (n + 1)) / n
    for i in range(n):
        z0 = plinth + 0.004 + i * (dh + 0.004)
        g.add(box_ext(-w / 2 + 0.004, -d / 2 - 0.006, z0, w / 2 - 0.004, -d / 2 + 0.012, z0 + dh, bevel=0.003), m, grain=0)
        for kx in ((-w * 0.25, w * 0.25) if w > 0.6 else (0,)):
            g.add(lathe([(0.0, 0.0), (0.012, 0.0), (0.008, 0.012), (0.016, 0.022), (0.0, 0.026)], seg=16), M[knob],
                  rx=pi / 2, loc=(kx, -d / 2 - 0.006, z0 + dh / 2))
    g.add(box_ext(-w / 2, d / 2 - 0.005, 0, w / 2, d / 2, h - 0.02), m)
    return g


def ivar(w=0.42, d=0.30, h=1.79):
    g = Geo()
    m = M['wood_pine']
    for sx in (-w / 2 + 0.017, w / 2 - 0.017):
        for sy in (-d / 2 + 0.017, d / 2 - 0.017):
            g.add(box(0.034, 0.034, h, at=(sx, sy, 0), bevel=0.003), m, grain=2)
        for z in (0.12, h - 0.06):
            g.add(box(0.02, d - 0.03, 0.045, at=(sx, 0, z)), m, grain=1)
    for z in (0.15, 0.55, 0.95, 1.35, h - 0.02):
        g.add(box(w - 0.07, d - 0.01, 0.018, at=(0, 0, z), bevel=0.002), m, grain=0)
    g.add(rbox(0.26, 0.20, 0.16, at=(0, 0, 0.568), r=0.01, seg=2), M['rattan'])
    for i in range(5):
        g.add(box(0.03, 0.18, 0.24, at=(-0.12 + i * 0.033, 0.0, 0.968), bevel=0.002),
              M[('book_a', 'book_c', 'book_e', 'book_b', 'book_d')[i]])
    return g


def sideboard():
    """White sideboard with oak top: door on the left, three drawers on the right."""
    g = Geo()
    w, d, h = 0.80, 0.40, 0.90
    b = M['white_furn']
    g.add(box_ext(-w / 2, -d / 2 + 0.01, 0.06, w / 2, d / 2, h - 0.025, bevel=0.002), b)
    g.add(box_ext(-w / 2 + 0.03, -d / 2 + 0.04, 0, w / 2 - 0.03, d / 2 - 0.02, 0.06), b)
    g.add(box_ext(-w / 2 - 0.01, -d / 2 - 0.005, h - 0.025, w / 2 + 0.01, d / 2, h, bevel=0.003), M['wood_oak'], grain=0)
    g.add(box_ext(-w / 2 + 0.004, -d / 2 - 0.008, 0.065, -0.004, -d / 2 + 0.01, h - 0.03, bevel=0.003), b)
    g.add(box(0.012, 0.012, 0.12, at=(-0.03, -d / 2 - 0.015, 0.55)), M['metal_grey'])
    for i in range(3):
        z0 = 0.065 + i * 0.27
        g.add(box_ext(0.004, -d / 2 - 0.008, z0, w / 2 - 0.004, -d / 2 + 0.01, z0 + 0.264, bevel=0.003), b)
        g.add(box(0.12, 0.012, 0.012, at=(w / 4, -d / 2 - 0.015, z0 + 0.20)), M['metal_grey'])
    # mirror leaning on the wall
    g.add(box(0.42, 0.02, 0.54, at=(0, 0.12, h), bevel=0.004), M['wood_oak'], rx=-0.12)
    g.add(box(0.37, 0.004, 0.49, at=(0, 0.105, h + 0.025)), M['mirror'], rx=-0.12)
    return g


def towel_ladder():
    g = Geo()
    m = M['bamboo']
    for sx in (-0.21, 0.21):
        g.add(cyl(0.016, 1.62, at=(sx, 0, 0), seg=12), m)
    for i in range(5):
        g.add(cyl(0.011, 0.42, at=(-0.21, 0, 0.30 + i * 0.30), seg=10, axis='X'), m)
    g.add(rbox(0.36, 0.05, 0.42, at=(0, -0.02, 0.96), r=0.02, seg=2), M['fab_linen'])
    return g


def rigga():
    """IKEA RIGGA clothes rack (white), rail along X."""
    g = Geo()
    m = M['metal_white']
    for sx in (-0.52, 0.52):
        g.add(box(0.04, 0.46, 0.03, at=(sx, 0, 0.03), bevel=0.008), m)
        for sy in (-0.2, 0.2):
            g.add(cyl(0.022, 0.03, at=(sx, sy, 0), seg=12), M['plastic_dark'])
        g.add(cyl(0.014, 1.60, at=(sx, 0, 0.05), seg=12), m)
    g.add(cyl(0.013, 1.08, at=(-0.54, 0, 1.63), seg=12, axis='X'), m)
    g.add(cyl(0.010, 1.04, at=(-0.52, 0, 0.18), seg=10, axis='X'), m)
    cols = ('fab_linen', 'fab_grey', 'fab_white', 'fab_charcoal', 'fab_linen', 'fab_white', 'fab_grey')
    for i, c in enumerate(cols):
        x = -0.38 + i * 0.12
        hh = 0.95 - (i % 3) * 0.12
        g.add(rbox(0.04, 0.44, hh, at=(x, 0, 1.58 - hh), r=0.015, seg=2), M[c])
        g.add(sweep([(x, -0.2, 1.55), (x, 0, 1.62), (x, 0.2, 1.55)], circle2d(0.004, 6)), M['wood_oak'])
    return g


# ============================================================ kitchen
def fridge():
    g = Geo()
    w = M['appliance_white']
    g.add(box_ext(-0.275, -0.25, 0.0, 0.275, 0.29, 1.43, bevel=0.012), w)
    g.add(box_ext(-0.272, -0.29, 0.03, 0.272, -0.25, 1.41, bevel=0.012), w)
    g.add(box(0.025, 0.02, 0.30, at=(0.235, -0.30, 0.95), bevel=0.006), M['plastic_grey'])
    for sx in (-0.22, 0.22):
        g.add(box(0.05, 0.05, 0.03, at=(sx, -0.2, 0)), M['plastic_dark'])
    # microwave + kettle on top
    g.add(rbox(0.46, 0.34, 0.26, at=(-0.03, 0.03, 1.43), r=0.01, seg=2), M['metal_grey'])
    g.add(box(0.31, 0.006, 0.20, at=(-0.09, -0.142, 1.46)), M['screen'])
    g.add(box(0.10, 0.006, 0.20, at=(0.135, -0.142, 1.46)), M['plastic_dark'])
    g.add(lathe([(0.0, 0.0), (0.075, 0.0), (0.085, 0.03), (0.08, 0.17), (0.055, 0.22), (0.0, 0.225)], seg=32),
          M['plastic_white'], loc=(0.16, 0.05, 1.69))
    g.add(tube([(0.235, 0.05, 1.72), (0.265, 0.05, 1.80), (0.235, 0.05, 1.89)], 0.012, sub=4), M['plastic_white'])
    return g


def raskog():
    g = Geo()
    m = M['metal_white']
    w, d = 0.35, 0.45
    for sx in (-w / 2 + 0.012, w / 2 - 0.012):
        for sy in (-d / 2 + 0.012, d / 2 - 0.012):
            g.add(cyl(0.011, 0.74, at=(sx, sy, 0.04), seg=10), m)
            g.add(cyl(0.022, 0.03, at=(sx, sy, 0.0), seg=12), M['plastic_dark'])
    for z in (0.12, 0.42, 0.72):
        g.add(box(w, d, 0.004, at=(0, 0, z)), m)
        for (sx, sy, a, b) in ((0, -d / 2, w, 0.004), (0, d / 2, w, 0.004), (-w / 2, 0, 0.004, d), (w / 2, 0, 0.004, d)):
            g.add(box(a, b, 0.05, at=(sx, sy, z), bevel=0.0015), m)
    g.add(box(0.2, 0.14, 0.08, at=(0, 0, 0.724)), M['ceramic_white'])
    return g


def cooker():
    """Free-standing 4-burner gas cooker 50 x 60 x 85, white enamel."""
    g = Geo()
    w = M['appliance_white']
    g.add(box_ext(-0.25, -0.28, 0.0, 0.25, 0.30, 0.85, bevel=0.006), w)
    g.add(box_ext(-0.25, -0.30, 0.74, 0.25, -0.28, 0.85, bevel=0.004), w)
    for i, x in enumerate((-0.18, -0.09, 0.0, 0.09, 0.18)):
        g.add(lathe([(0.0, 0.0), (0.02, 0.0), (0.02, 0.018), (0.012, 0.03), (0.0, 0.03)], seg=16), M['plastic_dark'],
              rx=pi / 2, loc=(x, -0.30, 0.795))
    g.add(box_ext(-0.215, -0.31, 0.12, 0.215, -0.28, 0.70, bevel=0.01), M['black_glass'])
    g.add(cyl(0.008, 0.40, at=(-0.20, -0.33, 0.66), seg=10, axis='X'), M['chrome'])
    for sx in (-0.2, 0.2):
        g.add(box(0.02, 0.025, 0.02, at=(sx, -0.32, 0.65)), M['chrome'])
    g.add(box_ext(-0.24, -0.29, 0.02, 0.24, -0.28, 0.10, bevel=0.004), w)
    for x in (-0.12, 0.12):
        for y in (-0.13, 0.15):
            r = 0.05 if (x < 0) == (y < 0) else 0.04
            g.add(cyl(r, 0.012, at=(x, y, 0.85), seg=28), M['cast_iron'])
            g.add(cyl(r * 0.75, 0.018, at=(x, y, 0.85), seg=24), M['metal_black'])
    for x in (-0.12, 0.12):
        for k in range(3):
            g.add(box(0.012, 0.52, 0.012, at=(x - 0.07 + k * 0.07, 0.01, 0.875)), M['cast_iron'])
        g.add(box(0.21, 0.012, 0.012, at=(x, -0.25, 0.875)), M['cast_iron'])
        g.add(box(0.21, 0.012, 0.012, at=(x, 0.27, 0.875)), M['cast_iron'])
    return g


def base_cabinets(w, doors, sink_at=None, d=0.60, h=0.88):
    """Kitchen base run: cherry fronts, marble-look worktop, optional inset stainless sink at x=sink_at."""
    g = Geo()
    car = M['white_furn']
    g.add(box_ext(-w / 2, -d / 2 + 0.05, 0.10, w / 2, d / 2, h - 0.03), car)
    g.add(box_ext(-w / 2, -d / 2 + 0.06, 0.0, w / 2, d / 2, 0.10), M['plastic_dark'])
    dw = w / doors
    for i in range(doors):
        x0 = -w / 2 + i * dw
        g.add(box_ext(x0 + 0.002, -d / 2 + 0.03, 0.10, x0 + dw - 0.002, -d / 2 + 0.05, h - 0.035, bevel=0.003), M['wood_cherry'], grain=2)
        kx = x0 + (dw - 0.05 if i % 2 == 0 else 0.05)
        g.add(lathe([(0.0, 0.0), (0.012, 0.0), (0.008, 0.012), (0.015, 0.022), (0.0, 0.025)], seg=14), M['brass'],
              rx=pi / 2, loc=(kx, -d / 2 + 0.03, h - 0.12))
    top = M['marble']
    tz0, tz1 = h - 0.03, h
    y0, y1 = -d / 2 - 0.02, d / 2
    if sink_at is None:
        g.add(box_ext(-w / 2, y0, tz0, w / 2, y1, tz1, bevel=0.004), top)
    else:
        sx0, sx1, sy0, sy1 = sink_at - 0.20, sink_at + 0.20, -0.20, 0.16
        g.add(box_ext(-w / 2, y0, tz0, sx0 - 0.02, y1, tz1, bevel=0.004), top)
        g.add(box_ext(sx1 + 0.02, y0, tz0, w / 2, y1, tz1, bevel=0.004), top)
        g.add(box_ext(sx0 - 0.02, y0, tz0, sx1 + 0.02, sy0 - 0.02, tz1, bevel=0.002), top)
        g.add(box_ext(sx0 - 0.02, sy1 + 0.02, tz0, sx1 + 0.02, y1, tz1, bevel=0.002), top)
        steel = M['steel']
        g.add(box_ext(sx0 - 0.02, sy0 - 0.02, tz1, sx0, sy1 + 0.02, tz1 + 0.004), steel)
        g.add(box_ext(sx1, sy0 - 0.02, tz1, sx1 + 0.02, sy1 + 0.02, tz1 + 0.004), steel)
        g.add(box_ext(sx0, sy0 - 0.02, tz1, sx1, sy0, tz1 + 0.004), steel)
        g.add(box_ext(sx0, sy1, tz1, sx1, sy1 + 0.02, tz1 + 0.004), steel)
        g.add(open_box(sx1 - sx0, sy1 - sy0, 0.17, at=(sink_at, (sy0 + sy1) / 2, tz1 - 0.17)), steel)
        # mixer tap
        tx, ty = sink_at, sy1 + 0.07
        g.add(cyl(0.025, 0.06, at=(tx, ty, tz1), seg=20), M['chrome'])
        g.add(tube([(tx, ty, tz1 + 0.05), (tx, ty, tz1 + 0.24), (tx, ty - 0.08, tz1 + 0.30), (tx, ty - 0.17, tz1 + 0.22)], 0.011, sub=6), M['chrome'])
        g.add(box(0.012, 0.09, 0.012, at=(tx, ty + 0.03, tz1 + 0.07), bevel=0.004), M['chrome'], rx=-0.4)
    return g


def wall_cabinets(w, units, d=0.32, h=0.70):
    """units: list of 'glass' / 'wood' / 'open'. Origin at the bottom centre."""
    g = Geo()
    car = M['wood_cherry']
    uw = w / len(units)
    g.add(box_ext(-w / 2, -d / 2, 0, w / 2, d / 2, 0.018), car, grain=0)
    g.add(box_ext(-w / 2, -d / 2, h - 0.018, w / 2, d / 2, h), car, grain=0)
    g.add(box_ext(-w / 2, d / 2 - 0.008, 0, w / 2, d / 2, h), M['white_furn'])
    for i in range(len(units) + 1):
        x = -w / 2 + i * uw
        g.add(box_ext(x - 0.009, -d / 2, 0, x + 0.009, d / 2, h), car, grain=2)
    for i, kind in enumerate(units):
        x0, x1 = -w / 2 + i * uw + 0.01, -w / 2 + (i + 1) * uw - 0.01
        g.add(box_ext(x0, -d / 2 + 0.02, h * 0.5, x1, d / 2, h * 0.5 + 0.015), M['white_furn'])
        if kind == 'open':
            for j in range(4):
                g.add(lathe([(0, 0), (0.1, 0), (0.12, 0.02), (0, 0.02)], seg=24), M['ceramic_white'], loc=((x0 + x1) / 2, 0, 0.02 + j * 0.022))
            continue
        if kind == 'glass':
            fr = M['wood_cherry']
            g.add(box_ext(x0, -d / 2 - 0.02, 0.0, x0 + 0.05, -d / 2, h), fr)
            g.add(box_ext(x1 - 0.05, -d / 2 - 0.02, 0.0, x1, -d / 2, h), fr)
            g.add(box_ext(x0, -d / 2 - 0.02, 0.0, x1, -d / 2, 0.05), fr)
            g.add(box_ext(x0, -d / 2 - 0.02, h - 0.05, x1, -d / 2, h), fr)
            g.add(box_ext(x0 + 0.05, -d / 2 - 0.012, 0.05, x1 - 0.05, -d / 2 - 0.008, h - 0.05), M['glass'])
            for j in range(3):
                g.add(cyl(0.035, 0.09, at=(x0 + 0.06 + j * 0.08, 0.0, h * 0.5 + 0.015), seg=20), M['glass_clear'])
            for j in range(5):
                g.add(lathe([(0, 0), (0.1, 0), (0.12, 0.02), (0, 0.02)], seg=24), M['ceramic_white'], loc=((x0 + x1) / 2, 0.02, 0.02 + j * 0.02))
        else:
            g.add(box_ext(x0, -d / 2 - 0.02, 0.0, x1, -d / 2, h, bevel=0.003), M['wood_cherry'], grain=2)
            g.add(lathe([(0.0, 0.0), (0.012, 0.0), (0.008, 0.012), (0.015, 0.022), (0.0, 0.025)], seg=14), M['brass'],
                  rx=pi / 2, loc=(x0 + 0.05 if i % 2 else x1 - 0.05, -d / 2 - 0.02, 0.08))
    return g


def fold_table():
    g = Geo()
    g.add(box(0.70, 0.40, 0.03, at=(0, 0, 0.72), bevel=0.004), M['laminate_red'])
    for sx in (-0.28, 0.28):
        g.add(sweep([(sx, 0.20, 0.45), (sx, 0.20, 0.72), (sx, -0.12, 0.72), (sx, 0.20, 0.45)], rect2d(0.02, 0.004)), M['metal_grey'])
    g.add(lathe([(0.0, 0.0), (0.1, 0.0), (0.13, 0.05), (0.0, 0.05)], seg=32), M['wood_oak'], loc=(0.12, -0.02, 0.75))
    for k, (x, y) in enumerate(((0.08, -0.02), (0.15, 0.02), (0.13, -0.06))):
        g.add(lathe([(0, 0), (0.03, 0.005), (0.035, 0.03), (0.03, 0.055), (0, 0.06)], seg=16), M['fruit_' + 'ab'[k % 2]],
              loc=(x, y, 0.765))
    return g


def wall_sconce():
    g = Geo()
    g.add(cyl(0.05, 0.02, seg=24, axis='Y'), M['plastic_white'], loc=(0, 0.01, 0))
    g.add(lathe([(0.0, -0.06), (0.09, -0.04), (0.10, 0.0), (0.0, 0.0)], seg=32), M['glass_glow'], rx=pi / 2, loc=(0, -0.0, 0))
    return g


# ============================================================ bathroom / wc
def bathtub(w=1.50, d=0.70, h=0.55):
    g = Geo()
    outer = box(w, d, h, at=(0, 0, 0), bevel=0.02, seg=3)
    inner = box(w - 0.14, d - 0.14, h, at=(0, 0, 0.12), bevel=0.06, seg=6)
    g.add(boolean(outer, inner), M['enamel'])
    g.add(box(0.06, 0.06, 0.006, at=(-w / 2 + 0.22, 0, 0.12)), M['chrome'])
    return g


def shower_mixer():
    """Wall mixer with spout, hose and hand shower. Origin on the wall, front -Y."""
    g = Geo()
    c = M['chrome']
    g.add(cyl(0.028, 0.22, at=(-0.11, -0.05, 0.0), seg=20, axis='X'), c)
    for x in (-0.12, 0.12):
        g.add(cyl(0.03, 0.04, at=(x - 0.02, -0.05, 0), seg=20, axis='X'), c)
        g.add(cyl(0.012, 0.05, at=(x, -0.05, 0.0), seg=12, axis='Y'), c, loc=(0, 0.05, 0))
    g.add(tube([(0.0, -0.06, -0.01), (0.0, -0.13, -0.04), (0.0, -0.16, -0.06)], 0.012, sub=4), c)
    g.add(tube([(0.02, -0.06, -0.02), (0.10, -0.12, -0.20), (0.30, -0.10, -0.25), (0.42, -0.06, 0.40), (0.44, -0.06, 0.95)], 0.007, sub=6), c)
    g.add(box(0.04, 0.05, 0.03, at=(0.44, -0.025, 1.0)), c)
    g.add(lathe([(0.0, 0.0), (0.016, 0.0), (0.016, 0.16), (0.045, 0.22), (0.045, 0.24), (0.0, 0.24)], seg=24), c, rx=0.2, loc=(0.44, -0.07, 0.96))
    return g


def toilet():
    """Floor standing pan in front of a concealed cistern box. Origin at the wall, pan faces -Y."""
    g = Geo()
    e = M['enamel']
    ped = lathe([(0.0, 0.0), (0.12, 0.0), (0.105, 0.12), (0.12, 0.30), (0.17, 0.38), (0.0, 0.38)], seg=40)
    xform(ped, scale=(1.0, 1.45, 1.0))
    g.add(ped, e, loc=(0, -0.29, 0))
    g.add(box(0.22, 0.20, 0.30, at=(0, -0.10, 0.08), bevel=0.04, seg=3), e)
    seat = lathe([(0.10, 0.0), (0.19, 0.0), (0.19, 0.02), (0.10, 0.02)], seg=40, cap_bottom=False)
    xform(seat, scale=(1.0, 1.32, 1.0))
    g.add(seat, M['plastic_white'], loc=(0, -0.30, 0.38))
    lid = cyl(0.185, 0.018, seg=40, bevel=0.008)
    xform(lid, scale=(1.0, 1.3, 1.0))
    g.add(lid, M['plastic_white'], loc=(0, -0.30, 0.40))
    return g


def wc_basin():
    g = Geo()
    outer = box(0.36, 0.27, 0.14, at=(0, 0, 0), bevel=0.03, seg=4)
    inner = box(0.28, 0.18, 0.14, at=(0, -0.02, 0.04), bevel=0.05, seg=5)
    g.add(boolean(outer, inner), M['enamel'], loc=(0, 0, 0))
    g.add(cyl(0.018, 0.08, at=(0, 0.10, 0.14), seg=16), M['chrome'])
    g.add(tube([(0, 0.10, 0.20), (0, 0.06, 0.22), (0, 0.02, 0.19)], 0.009, sub=4), M['chrome'])
    g.add(cyl(0.02, 0.22, at=(0, 0.08, -0.22), seg=16), M['chrome'])
    g.add(tube([(0, 0.08, -0.22), (0, 0.10, -0.26), (0, 0.135, -0.26)], 0.018, sub=3), M['chrome'])
    return g


def paper_stand():
    g = Geo()
    c = M['chrome']
    g.add(cyl(0.09, 0.008, seg=28, bevel=0.003), c)
    g.add(tube([(0, 0, 0.0), (0, 0, 0.62), (0.08, 0, 0.62)], 0.006, sub=3), c)
    g.add(lathe([(0.02, 0.0), (0.055, 0.0), (0.055, 0.10), (0.02, 0.10)], seg=24, cap_top=True, cap_bottom=True), M['paper'],
          ry=pi / 2, loc=(0.03, 0, 0.62))
    g.add(lathe([(0.02, 0.0), (0.055, 0.0), (0.055, 0.10), (0.02, 0.10)], seg=24, cap_top=True, cap_bottom=True), M['paper'],
          loc=(0, 0, 0.30))
    return g


def basket():
    g = Geo()
    g.add(lathe([(0.0, 0.0), (0.18, 0.0), (0.19, 0.45), (0.185, 0.45), (0.175, 0.012), (0.0, 0.012)], seg=40), M['fab_grey'])
    g.add(rbox(0.30, 0.28, 0.06, at=(0, 0, 0.40), r=0.03, seg=3), M['fab_white'])
    return g


def wall_shelf(w=0.45, d=0.15):
    g = Geo()
    g.add(box(w, d, 0.025, bevel=0.003), M['wood_pine'], grain=0)
    for sx in (-w / 2 + 0.05, w / 2 - 0.05):
        g.add(box(0.02, d - 0.02, 0.10, at=(sx, 0.01, -0.10)), M['wood_pine'])
    return g


# ============================================================ hall
def entry_door_leaf(w, h=2.04, t=0.06):
    """Steel entrance door with 6 raised panels on both faces. Origin at the hinge edge, leaf along +X."""
    g = Geo()
    m = M['door_entry']
    g.add(box(w, t, h, at=(w / 2, 0, 0), bevel=0.004), m)
    cols = (0.27, 0.73)
    rows = ((1.62, 1.92), (0.98, 1.52), (0.16, 0.88))
    for side in (-1, 1):
        for cx in cols:
            for z0, z1 in rows:
                g.add(box(w * 0.36, 0.006, z1 - z0, at=(w * cx, side * (t / 2 + 0.002), z0), bevel=0.004), m)
    plate = M['bronze']
    for side in (-1, 1):
        g.add(box(0.05, 0.012, 0.30, at=(w - 0.08, side * (t / 2 + 0.006), 0.86), bevel=0.004), plate)
        g.add(box(0.13, 0.018, 0.02, at=(w - 0.14, side * (t / 2 + 0.03), 1.05), bevel=0.006), plate)
        g.add(cyl(0.016, 0.02, at=(w - 0.08, side * (t / 2 + 0.01), 0.90), seg=16, axis='Y'), M['chrome'], loc=(0, 0, 0))
    g.add(cyl(0.008, t + 0.01, at=(w / 2, -t / 2 - 0.005, 1.55), seg=12, axis='Y'), M['chrome'])
    return g


def interior_leaf(w, kind='flush', h=2.00, t=0.04):
    """Interior door leaf. Origin at hinge edge, leaf along +X. kind: flush | glazed | vent."""
    g = Geo()
    m = M.get('door_leaf', M['door_white'])
    if kind == 'glazed':
        st = 0.11
        g.add(box(st, t, h, at=(st / 2, 0, 0), bevel=0.003), m)
        g.add(box(st, t, h, at=(w - st / 2, 0, 0), bevel=0.003), m)
        for z0, z1 in ((0.0, 0.18), (0.95, 1.08), (h - 0.14, h)):
            g.add(box(w - 2 * st, t, z1 - z0, at=(w / 2, 0, z0), bevel=0.003), m)
        for z0, z1 in ((0.18, 0.95), (1.08, h - 0.14)):
            g.add(box(w - 2 * st, 0.006, z1 - z0, at=(w / 2, 0, z0)), M['glass_frosted'])
            for side in (-1, 1):
                for (a, b) in ((z0, z0 + 0.02), (z1 - 0.02, z1)):
                    g.add(box(w - 2 * st, 0.012, 0.02, at=(w / 2, side * 0.008, a)), m)
    else:
        g.add(box(w, t, h, at=(w / 2, 0, 0), bevel=0.003), m)
        if kind == 'vent':
            for side in (-1, 1):
                g.add(box(0.36, 0.004, 0.10, at=(w / 2, side * (t / 2 + 0.001), 0.06)), M['plastic_white'])
                for k in range(6):
                    g.add(box(0.33, 0.004, 0.006, at=(w / 2, side * (t / 2 + 0.003), 0.075 + k * 0.014)), M['plastic_grey'])
    c = M['chrome']
    for side in (-1, 1):
        g.add(box(0.04, 0.008, 0.18, at=(w - 0.07, side * (t / 2 + 0.004), 0.95), bevel=0.003), c)
        g.add(tube([(w - 0.07, side * (t / 2 + 0.01), 1.06), (w - 0.07, side * (t / 2 + 0.05), 1.06), (w - 0.18, side * (t / 2 + 0.055), 1.06)], 0.008, sub=4), c)
    return g


def built_in_cabinet(w=1.38, d=0.40, h=2.58):
    g = Geo()
    wm = M['white_gloss']
    g.add(box_ext(-w / 2, -d / 2 + 0.02, 0, w / 2, d / 2, h), M['white_furn'])
    for z0, z1 in ((0.02, 1.94), (1.96, h - 0.01)):
        for i in range(2):
            x0 = -w / 2 + i * w / 2 + 0.003
            x1 = x0 + w / 2 - 0.006
            g.add(box_ext(x0, -d / 2, z0, x1, -d / 2 + 0.02, z1, bevel=0.003), wm)
            kx = x1 - 0.06 if i == 0 else x0 + 0.06
            kz = z0 + 0.15 if z1 > 2 else 0.95
            g.add(lathe([(0.0, 0.0), (0.012, 0.0), (0.006, 0.012), (0.016, 0.024), (0.0, 0.03)], seg=16), M['brass'],
                  rx=pi / 2, loc=(kx, -d / 2, kz))
    return g


def open_shelf(w=0.80, d=0.35, h=1.0, mat='wood_black'):
    g = Geo()
    m = M[mat]
    for sx in (-w / 2 + 0.009, w / 2 - 0.009):
        g.add(box(0.018, d, h, at=(sx, 0, 0), bevel=0.002), m)
    for z in (0.0, 0.33, 0.66, h - 0.018):
        g.add(box(w, d, 0.018, at=(0, 0, z), bevel=0.002), m)
    g.add(box(w, 0.006, h, at=(0, d / 2 - 0.003, 0)), m)
    for k, x in enumerate((-0.25, 0.0, 0.22)):
        g.add(rbox(0.22, 0.28, 0.09, at=(x, 0, 0.018), r=0.03, seg=3), M[('fab_charcoal', 'leather', 'fab_linen')[k]])
    g.add(rbox(0.30, 0.25, 0.20, at=(-0.18, 0, 0.348), r=0.01, seg=2), M['rattan'])
    return g


def paneling(L, h=2.0):
    """Vertical pine boards along X, front faces -Y."""
    g = Geo()
    n = int(L / 0.096)
    bw = L / n
    for i in range(n):
        g.add(box(bw - 0.004, 0.014, h, at=(-L / 2 + (i + 0.5) * bw, 0, 0), bevel=0.002), M['wood_pine'], grain=2)
    g.add(box(L, 0.03, 0.04, at=(0, -0.008, h), bevel=0.004), M['wood_pine'], grain=0)
    return g


def overhead_cabinet(L, d=0.36, h=0.56):
    g = Geo()
    m = M['wood_cherry']
    g.add(box(L, d, h, at=(0, 0, 0), bevel=0.003), m, grain=0)
    n = 3
    for i in range(n):
        x0 = -L / 2 + i * L / n + 0.004
        g.add(box_ext(x0, -d / 2 - 0.018, 0.004, x0 + L / n - 0.008, -d / 2, h - 0.004, bevel=0.003), m, grain=2)
        g.add(lathe([(0.0, 0.0), (0.012, 0.0), (0.006, 0.012), (0.014, 0.022), (0.0, 0.026)], seg=14), M['brass'],
              rx=pi / 2, loc=(x0 + L / n / 2, -d / 2 - 0.018, 0.06))
    return g


def coat_rack(L=1.0):
    g = Geo()
    g.add(box(L, 0.025, 0.13, at=(0, 0, 0), bevel=0.004), M['wood_oak'], grain=0)
    for i in range(6):
        x = -L / 2 + 0.08 + i * (L - 0.16) / 5
        g.add(tube([(x, -0.01, 0.06), (x, -0.06, 0.05), (x, -0.075, 0.09)], 0.008, sub=4), M['metal_black'])
    return g


def dome_pendant(drop, r=0.17, color='glass_glow'):
    g = Geo()
    g.add(cyl(0.045, 0.02, at=(0, 0, -0.02), seg=24), M['plastic_white'])
    g.add(cyl(0.004, drop - 0.2, at=(0, 0, -drop + 0.2), seg=6), M['metal_black'])
    g.add(lathe([(0.03, -drop + 0.2), (0.07, -drop + 0.17), (r * 0.95, -drop + 0.05), (r, -drop), (r - 0.004, -drop),
                 (r * 0.93, -drop + 0.05), (0.065, -drop + 0.165), (0.028, -drop + 0.195)], seg=48), M[color])
    g.add(lathe([(0.0, -drop + 0.03), (0.035, -drop + 0.06), (0.035, -drop + 0.1), (0.0, -drop + 0.12)], seg=16), M['bulb'])
    return g


def flush_light(r=0.16):
    g = Geo()
    g.add(lathe([(0.0, -0.08), (r * 0.7, -0.075), (r, -0.03), (r, 0.0), (0.0, 0.0)], seg=48), M['glass_glow'])
    return g


def brass_sconce():
    g = Geo()
    g.add(cyl(0.05, 0.03, seg=24, axis='Y'), M['brass'], loc=(0, 0.015, 0))
    g.add(tube([(0, -0.03, 0), (0, -0.09, -0.02), (0, -0.12, -0.08)], 0.008, sub=4), M['brass'])
    g.add(lathe([(0.0, 0.0), (0.03, 0.01), (0.04, 0.06), (0.025, 0.1), (0.0, 0.11)], seg=24), M['bulb'], loc=(0, -0.12, -0.20))
    return g


# ============================================================ loggia
def railing(L, h=1.02):
    """Black steel railing along X, posts every ~1.3 m, balusters every 0.11 m."""
    g = Geo()
    m = M['metal_black']
    g.add(box(L, 0.05, 0.035, at=(0, 0, h - 0.035), bevel=0.006), m)
    g.add(box(L, 0.03, 0.03, at=(0, 0, 0.12)), m)
    n = int(L / 0.11)
    for i in range(n + 1):
        x = -L / 2 + 0.03 + i * (L - 0.06) / n
        g.add(box(0.014, 0.014, h - 0.17, at=(x, 0, 0.13)), m)
    for x in (-L / 2 + 0.025, L / 2 - 0.025):
        g.add(box(0.05, 0.05, h, at=(x, 0, 0), bevel=0.004), m)
    return g


def pot(r, h, matname):
    """Planter pot with a soil disc; origin at the bottom centre."""
    g = Geo()
    g.add(lathe([(0.0, 0.0), (r * 0.72, 0.0), (r * 0.75, 0.01), (r, h - 0.02), (r * 1.04, h - 0.015), (r * 1.04, h),
                 (r * 0.94, h), (r * 0.9, h - 0.03), (0.0, h - 0.03)], seg=40), M[matname])
    g.add(cyl(r * 0.9, 0.005, at=(0, 0, h - 0.035), seg=32), M['soil'])
    return g


def bamboo_shelf(w=0.62, d=0.30, h=0.78):
    """Three-tier bamboo shelf (under the living-room window)."""
    g = Geo()
    m = M['bamboo']
    for sx in (-w / 2 + 0.015, w / 2 - 0.015):
        for sy in (-d / 2 + 0.015, d / 2 - 0.015):
            g.add(cyl(0.014, h, at=(sx, sy, 0), seg=12), m)
    for z in (0.10, 0.42, h - 0.02):
        for k in range(7):
            g.add(box(w - 0.02, (d - 0.03) / 7 - 0.004, 0.012, at=(0, -d / 2 + 0.015 + (k + 0.5) * (d - 0.03) / 7, z), bevel=0.002), m, grain=0)
        g.add(cyl(0.008, w - 0.03, at=(-w / 2 + 0.015, -d / 2 + 0.015, z + 0.006), seg=8, axis='X'), m)
        g.add(cyl(0.008, w - 0.03, at=(-w / 2 + 0.015, d / 2 - 0.015, z + 0.006), seg=8, axis='X'), m)
    g.add(rbox(0.30, 0.22, 0.17, at=(-0.1, 0, 0.112), r=0.01, seg=2), M['rattan'])
    for i in range(4):
        g.add(box(0.025, 0.18, 0.22 - i * 0.02, at=(0.12 + i * 0.03, 0, 0.432), bevel=0.002), M[('book_b', 'book_e', 'book_a', 'book_d')[i]])
    return g
