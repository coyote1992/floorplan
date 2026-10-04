"""Furniture for the garden flat (flat 2). Same conventions as furniture.py:
origin = centre of the footprint on the floor, front faces -Y, width along X, metres."""
from math import pi, sin, cos, radians
from mathutils import Vector
from lib import Geo, box, box_ext, cyl, lathe, sweep, tube, rect2d, circle2d, smooth_path, grid_surface, xform, rng
from furniture import M, rbox


# ============================================================ living room
def sofa_corner(L=2.70, D=0.95, CD=1.62):
    """Teal and slate-grey corner sofa, chaise on the left (-X) coming forward (-Y)."""
    g = Geo()
    teal, slate = M['fab_teal'], M['fab_slate']
    x0, x1 = -L / 2, L / 2
    yb, yf = D / 2, -D / 2                  # back, front of the main part
    yc = D / 2 - CD                         # front of the chaise
    cw = 0.95                               # chaise width
    # plinth band (teal) and seat base
    g.add(box_ext(x0, yf, 0.02, x1, yb, 0.30, bevel=0.03, seg=3), teal)
    g.add(box_ext(x0, yc, 0.02, x0 + cw, yf + 0.02, 0.30, bevel=0.03, seg=3), teal)
    g.add(box_ext(x0 + 0.02, yf - 0.004, 0.10, x1 - 0.02, yf + 0.01, 0.13), slate)            # slate piping band
    g.add(box_ext(x0 - 0.004, yc + 0.02, 0.10, x0 + 0.01, yb - 0.02, 0.13), slate)
    # seat cushions (slate)
    g.add(box_ext(x0 + cw, yf, 0.30, x1 - 0.20, yb - 0.24, 0.47, bevel=0.06, seg=5), slate)
    g.add(box_ext(x0 + 0.02, yc, 0.30, x0 + cw, yb - 0.24, 0.47, bevel=0.06, seg=5), slate)
    # back: teal frame + mixed back cushions
    g.add(box_ext(x0, yb - 0.24, 0.30, x1, yb, 0.62, bevel=0.07, seg=5), teal)
    n = 3
    bw = (L - 0.30) / n
    for i in range(n):
        cx = x0 + 0.08 + bw * (i + 0.5)
        g.add(rbox(bw - 0.03, 0.20, 0.36, r=0.07, seg=5, origin='center'), slate if i == 1 else teal,
              rx=-0.18, loc=(cx, yb - 0.22, 0.66))
    # arm on the right, low side on the chaise
    g.add(box_ext(x1 - 0.22, yf, 0.30, x1, yb - 0.1, 0.60, bevel=0.08, seg=5), teal)
    g.add(box_ext(x0 - 0.01, yc, 0.30, x0 + 0.12, yb - 0.24, 0.44, bevel=0.05, seg=4), teal)
    for x, y in ((x0 + 0.05, yc + 0.05), (x1 - 0.05, yb - 0.05), (x1 - 0.05, yf + 0.05), (x0 + 0.05, yb - 0.05)):
        g.add(cyl(0.02, 0.02, at=(x, y, 0), seg=10), M['metal_black'])
    # throw pillows and a rolled blanket
    for x, mname, rz in ((x0 + 0.45, 'fab_orange', 0.25), (x1 - 0.95, 'fab_linen', -0.1), (x1 - 0.60, 'fab_blue', 0.05),
                         (x1 - 0.42, 'fab_peach', -0.15)):
        g.add(rbox(0.44, 0.13, 0.42, r=0.06, seg=5, origin='center'), M[mname], rx=-0.32, rz=rz,
              loc=(x, yb - 0.36, 0.70))
    g.add(cyl(0.07, 0.36, at=(x0 + 0.55, yc + 0.80, 0.54), seg=18, axis='X'), M['fab_white'], rz=0.4)
    return g


def wall_unit(W=3.60, H=2.50, D=0.36):
    """Floor-to-ceiling spruce wall unit: glass cabinet, shelves, cubby grid, top row of open boxes."""
    g = Geo()
    w = M['wood_spruce']
    t = 0.022
    top_h = 0.34
    g.add(box_ext(-W / 2, D / 2 - 0.01, 0, W / 2, D / 2, H), w)                         # back panel
    g.add(box_ext(-W / 2, -D / 2 + 0.03, 0, W / 2, D / 2, 0.07), w)                     # plinth
    g.add(box_ext(-W / 2, -D / 2, H - t, W / 2, D / 2, H, bevel=0.002), w, grain=0)       # top
    zt = H - top_h
    g.add(box_ext(-W / 2, -D / 2, zt - t, W / 2, D / 2, zt, bevel=0.002), w, grain=0)     # top-row floor
    # top row of boxes, uprights every ~0.6 m, with dark blue bowls
    nt = 6
    for i in range(nt + 1):
        x = -W / 2 + i * W / nt
        g.add(box_ext(x - t / 2, -D / 2, zt, x + t / 2, D / 2, H - t), w, grain=2)
    for i in range(nt):
        x = -W / 2 + (i + 0.5) * W / nt
        g.add(lathe([(0.0, 0.0), (0.05, 0.0), (0.08, 0.05), (0.075, 0.055), (0.0, 0.01)], seg=24), M['bowl_blue'],
              loc=(x, 0, zt))
    bays = [(0.50, 'glass'), (0.70, 'shelves'), (0.86, 'open'), (0.70, 'grid'), (0.84, 'shelves')]
    scale = W / sum(b[0] for b in bays)
    x = -W / 2
    for bw, kind in bays:
        bw *= scale
        g.add(box_ext(x, -D / 2, 0.07, x + t, D / 2, zt - t), w, grain=2)
        xa, xb = x + t, x + bw
        if kind == 'glass':
            for z in (0.07, 0.55, 1.03, 1.51):
                g.add(box_ext(xa, -D / 2 + 0.03, z + 0.4, xb, D / 2 - 0.02, z + 0.408), M['glass_clear'])
            g.add(box_ext(xa + 0.01, -D / 2 - 0.02, 0.08, xa + 0.04, -D / 2, zt - 0.03), w)
            g.add(box_ext(xb - 0.04, -D / 2 - 0.02, 0.08, xb - 0.01, -D / 2, zt - 0.03), w)
            g.add(box_ext(xa + 0.04, -D / 2 - 0.015, 0.10, xb - 0.04, -D / 2 - 0.005, zt - 0.05), M['glass_clear'])
        elif kind == 'shelves':
            for z in (0.40, 0.75, 1.10, 1.45, 1.80):
                g.add(box_ext(xa, -D / 2, z, xb, D / 2 - 0.01, z + t), w, grain=0)
            # a narrow inner tower on one side
            g.add(box_ext(xa + 0.26, -D / 2, 0.07, xa + 0.26 + t, D / 2, zt - t), w, grain=2)
        elif kind == 'open':
            for z in (0.60, 1.20):
                g.add(box_ext(xa, -D / 2, z, xb, D / 2 - 0.01, z + t), w, grain=0)
            g.add(box(0.16, 0.02, 0.22, at=((xa + xb) / 2 - 0.08, 0.08, 1.20 + t), bevel=0.004), M['white_matt'], rx=0.08)
        elif kind == 'grid':
            for z in (0.36, 0.62, 0.88, 1.14, 1.40, 1.66):
                g.add(box_ext(xa, -D / 2, z, xb, D / 2 - 0.01, z + t), w, grain=0)
            for k in range(1, 3):
                xx = xa + k * (xb - xa) / 3
                g.add(box_ext(xx - t / 2, -D / 2, 0.07, xx + t / 2, D / 2, zt - t), w, grain=2)
        x += bw
    g.add(box_ext(W / 2 - t, -D / 2, 0.07, W / 2, D / 2, zt - t), w, grain=2)
    # a few objects: glass jar, books
    for i, c in enumerate(('book_b', 'book_e', 'book_a', 'book_c')):
        g.add(box(0.025, 0.2, 0.24 - i * 0.015, at=(W / 2 - 0.40 + i * 0.03, 0.02, 1.10 + t), bevel=0.002), M[c])
    g.add(cyl(0.045, 0.12, at=(-W / 2 + 0.80, 0, 1.45 + t), seg=20), M['glass_clear'])
    return g


def dining_table_white(w=1.30, d=0.80, h=0.75):
    g = Geo()
    g.add(box(w, d, 0.035, at=(0, 0, h - 0.035), bevel=0.004), M['white_gloss'])
    g.add(box_ext(-w / 2 + 0.04, -d / 2 + 0.04, h - 0.11, w / 2 - 0.04, d / 2 - 0.04, h - 0.035), M['white_gloss'])
    for sx in (-1, 1):
        for sy in (-1, 1):
            g.add(box(0.05, 0.05, h - 0.035, at=(sx * (w / 2 - 0.05), sy * (d / 2 - 0.05), 0), bevel=0.004), M['white_gloss'])
    for x in (-0.30, 0.30):
        g.add(box(0.38, 0.30, 0.004, at=(x, -0.12, h)), M['fab_linen'])
    return g


def conf_chair():
    """Beech frame chair with navy upholstered seat and back (dining chairs)."""
    g = Geo()
    b = M['wood_beech']
    for sx in (-0.21, 0.21):
        g.add(sweep(smooth_path([(sx, -0.22, 0.0), (sx, -0.21, 0.40), (sx, -0.05, 0.64), (sx, 0.18, 0.62), (sx, 0.22, 0.0)], 5),
                    rect2d(0.035, 0.04, 0.008, 2), normal_hint=(1, 0, 0)), b, grain=1)
    g.add(rbox(0.44, 0.44, 0.08, at=(0, -0.01, 0.40), r=0.03, seg=3), M['fab_navy'])
    g.add(rbox(0.44, 0.06, 0.36, r=0.03, seg=3, origin='center'), M['fab_navy'], rx=-0.12, loc=(0, 0.21, 0.76))
    return g


def wall_clock(r=0.72):
    """Wall-sticker clock: numerals 12, 3, 6, 9, dashes and hands. Plane at y=0 facing -Y, centre at z=0."""
    g = Geo()
    k = M['decal_black']
    t = 0.004

    def seg(x0, z0, x1, z1, wdt=0.012):
        dx, dz = x1 - x0, z1 - z0
        L = (dx * dx + dz * dz) ** 0.5
        a = -__import__('math').atan2(dz, dx)
        g.add(box(L, t, wdt, at=(0, 0, 0), origin='center'), k, ry=a, loc=((x0 + x1) / 2, -t / 2, (z0 + z1) / 2))

    def digit(dgt, cx, cz, s=0.055):
        # seven-segment glyph
        S7 = {'1': 'bc', '2': 'abged', '3': 'abgcd', '6': 'afgedc', '9': 'abcdfg'}[dgt]
        pts = {'a': ((-s, s * 2), (s, s * 2)), 'b': ((s, s * 2), (s, 0)), 'c': ((s, 0), (s, -s * 2)), 'd': ((-s, -s * 2), (s, -s * 2)),
               'e': ((-s, 0), (-s, -s * 2)), 'f': ((-s, s * 2), (-s, 0)), 'g': ((-s, 0), (s, 0))}
        for sgm in S7:
            (ax, az), (bx, bz) = pts[sgm]
            seg(cx + ax, cz + az, cx + bx, cz + bz, 0.016)
    digit('1', -0.115, r - 0.04)
    digit('2', 0.065, r - 0.04)
    digit('3', r - 0.02, 0)
    digit('6', 0, -r + 0.04)
    digit('9', -r + 0.02, 0)
    for h_ in (1, 2, 4, 5, 7, 8, 10, 11):
        a = radians(90 - h_ * 30)
        seg(cos(a) * (r - 0.08), sin(a) * (r - 0.08), cos(a) * r, sin(a) * r, 0.014)
    g.add(cyl(0.03, 0.02, at=(0, 0, 0), seg=20, axis='Y'), k, loc=(0, -0.02, 0))
    seg(0, 0, -0.30, 0.03, 0.022)                 # hour hand
    seg(0, 0, -0.12, -0.42, 0.016)                # minute hand
    return g


def chandelier(w=0.42, drop=0.55):
    """Square crystal chandelier hanging from the ceiling (origin at the ceiling)."""
    g = Geo()
    c = M['chrome']
    g.add(box(w + 0.06, w + 0.06, 0.03, at=(0, 0, -0.03)), c)
    g.add(box(w, w, 0.02, at=(0, 0, -0.12)), c)
    g.add(cyl(0.008, 0.09, at=(0, 0, -0.12), seg=8), c)
    n = 9
    for i in range(n):
        for j in range(n):
            if 0 < i < n - 1 and 0 < j < n - 1 and rng.random() < 0.55:
                continue
            x = -w / 2 + w * (i + 0.5) / n
            y = -w / 2 + w * (j + 0.5) / n
            L = drop - 0.18 - rng.random() * 0.12 if (i in (0, n - 1) or j in (0, n - 1)) else drop - 0.12
            g.add(cyl(0.006, L, at=(x, y, -0.12 - L), seg=6), M['crystal'])
    g.add(lathe([(0.0, -drop + 0.12), (0.05, -drop + 0.16), (0.05, -drop + 0.30), (0.0, -drop + 0.34)], seg=16), M['bulb'])
    return g


def runner(w, d, matname='fab_rugdark'):
    g = Geo()
    g.add(box(w, d, 0.008, bevel=0.003, seg=1), M[matname])
    return g


def picture(w, h, matname, frame='wood_oak', depth=0.02):
    """Framed print; front faces -Y, bottom at z=0."""
    g = Geo()
    g.add(box(w, depth, h, at=(0, 0, 0), bevel=0.003), M[frame])
    g.add(box(w - 0.04, 0.004, h - 0.04, at=(0, -depth / 2 - 0.001, 0.02)), M[matname])
    return g


def canvas(w, h, matname):
    g = Geo()
    g.add(box(w, 0.03, h, at=(0, 0, 0), bevel=0.004, seg=1), M[matname])
    return g


# ============================================================ bedroom (boho)
def mattress_floor(w=1.40, l=2.00):
    """Mattress on the floor along +Y (head at +Y), quilt and cushions."""
    g = Geo()
    g.add(rbox(w, l, 0.18, r=0.04, seg=4), M['fab_white'])
    g.add(rbox(w + 0.02, l * 0.62, 0.03, at=(0, -l * 0.17, 0.18), r=0.015, seg=3), M['quilt'])
    for x in (-w * 0.24, w * 0.24):
        g.add(rbox(0.48, 0.34, 0.13, at=(x, l / 2 - 0.22, 0.18), r=0.05, seg=4), M['fab_linen'])
    g.add(rbox(0.42, 0.12, 0.40, r=0.06, seg=5, origin='center'), M['fab_blue'], rx=-0.35, loc=(-w * 0.15, l / 2 - 0.06, 0.42))
    g.add(rbox(0.40, 0.12, 0.38, r=0.06, seg=5, origin='center'), M['fab_orange'], rx=-0.30, loc=(w * 0.22, l / 2 - 0.06, 0.41))
    return g


def macrame(w=0.80, h=1.70):
    """Macramé curtain: wooden rod, vertical cords with chevron knots. Plane at y=0, top at z=0."""
    g = Geo()
    cord = M['macrame']
    g.add(cyl(0.012, w + 0.12, at=(-w / 2 - 0.06, 0, 0), seg=10, axis='X'), M['wood_oak'])
    n = int(w / 0.028)
    for i in range(n):
        x = -w / 2 + (i + 0.5) * w / n
        L = h * (0.82 + 0.18 * abs(cos(pi * (i + 0.5) / n)))   # V-shaped hem
        g.add(box(0.006, 0.006, L, at=(x, 0, -L)), cord)
    for row in range(7):
        z = -0.12 - row * 0.19
        for side in (-1, 1):
            for k in range(5):
                x0 = side * (0.04 + k * 0.07)
                g.add(box(0.06, 0.012, 0.012, at=(0, 0, 0), origin='center'), cord, ry=side * 0.6,
                      loc=(x0, -0.004, z - k * 0.03))
    return g


def string_lights(L=1.6, sag=0.18, n=12):
    g = Geo()
    pts = [(-L / 2 + L * i / 20, 0, -sag * (1 - ((i - 10) / 10) ** 2)) for i in range(21)]
    g.add(tube(pts, 0.002, n=5, sub=1), M['metal_black'])
    for i in range(n):
        t = (i + 0.5) / n
        x = -L / 2 + L * t
        z = -sag * (1 - (2 * t - 1) ** 2)
        g.add(lathe([(0.0, 0.0), (0.012, 0.01), (0.012, 0.03), (0.0, 0.04)], seg=10), M['bulb'], loc=(x, -0.01, z - 0.05))
    return g


def loft_frame(W=2.60, D=1.00, Ht=2.05):
    """Pine sleeping/storage loft in the walk-in closet: posts, plank platform, hanging rail, ladder."""
    g = Geo()
    p = M['wood_pine']
    for x in (-W / 2 + 0.04, W / 2 - 0.04, -W / 2 + 1.0):
        for y in (-D / 2 + 0.04, D / 2 - 0.04):
            g.add(box(0.07, 0.07, Ht, at=(x, y, 0), bevel=0.004), p, grain=2)
    for y in (-D / 2 + 0.04, D / 2 - 0.04):
        g.add(box(W, 0.07, 0.12, at=(0, y, Ht - 0.12), bevel=0.004), p, grain=0)
    nb = int(W / 0.14)
    for i in range(nb):
        g.add(box(W / nb - 0.008, D, 0.022, at=(-W / 2 + (i + 0.5) * W / nb, 0, Ht), bevel=0.002), p, grain=1)
    g.add(cyl(0.014, W - 1.1, at=(-W / 2 + 1.04, 0.05, 1.62), seg=12, axis='X'), M['wood_dark'])
    g.add(box(0.95, D - 0.1, 0.022, at=(-W / 2 + 0.52, 0, 0.30), bevel=0.002), p, grain=0)
    for i, c in enumerate(('fab_linen', 'fab_grey', 'fab_white', 'fab_charcoal', 'fab_blue')):
        x = -W / 2 + 1.25 + i * 0.13
        g.add(rbox(0.04, 0.42, 0.85 - (i % 2) * 0.15, at=(x, 0.05, 1.60 - 0.85 + (i % 2) * 0.15), r=0.015, seg=2), M[c])
    # metal step ladder leaning on the platform edge
    lad = M['metal_grey']
    lx, base = W / 2 - 1.10, 0.30
    for sx in (-0.2, 0.2):
        g.add(sweep([(lx + sx, -D / 2 - base, 0), (lx + sx, -D / 2 + 0.02, Ht)], rect2d(0.03, 0.06)), lad)
    for k in range(7):
        t = (k + 0.5) / 7
        g.add(box(0.40, 0.10, 0.02, at=(lx, -D / 2 - base + (base + 0.02) * t, Ht * t)), lad)
    return g


# ============================================================ study (second room)
def sofa_bed_small(w=1.45, d=0.88):
    """Dark brown two-seat sofa bed with bentwood beech arms."""
    g = Geo()
    f = M['fab_brown']
    g.add(box_ext(-w / 2 + 0.07, -d / 2 + 0.02, 0.10, w / 2 - 0.07, d / 2, 0.42, bevel=0.04, seg=4), f)
    g.add(box_ext(-w / 2 + 0.07, d / 2 - 0.22, 0.42, w / 2 - 0.07, d / 2, 0.82, bevel=0.06, seg=5), f)
    for sx in (-1, 1):
        x = sx * (w / 2 - 0.035)
        path = smooth_path([(x, -d / 2 + 0.05, 0.02), (x, -d / 2 + 0.02, 0.45), (x, -d / 2 + 0.12, 0.60), (x, d / 2 - 0.15, 0.62),
                            (x, d / 2 - 0.05, 0.55), (x, d / 2 - 0.10, 0.02)], 6)
        g.add(sweep(path, rect2d(0.05, 0.06, 0.015, 2), normal_hint=(1, 0, 0)), M['wood_beech'], grain=1)
    for x, c, rz in ((-0.45, 'fab_peach', 0.1), (-0.25, 'fab_olive', -0.05), (0.0, 'fab_charcoal', 0.08), (0.45, 'fab_linen', -0.2)):
        g.add(rbox(0.40, 0.12, 0.38, r=0.06, seg=5, origin='center'), M[c], rx=-0.3, rz=rz, loc=(x, d / 2 - 0.32, 0.62))
    return g


def desk_simple(w=1.00, d=0.55, top='white_matt', legs='metal_black', h=0.75):
    g = Geo()
    g.add(box(w, d, 0.03, at=(0, 0, h - 0.03), bevel=0.003), M[top], grain=0)
    for sx in (-1, 1):
        for sy in (-1, 1):
            g.add(box(0.035, 0.035, h - 0.03, at=(sx * (w / 2 - 0.04), sy * (d / 2 - 0.04), 0)), M[legs])
    return g


def desk_dark(w=1.00, d=0.50, h=0.76):
    """Dark wood desk with a shelf and a laptop and lamp on it."""
    g = Geo()
    m = M['wood_walnut']
    g.add(box(w, d, 0.03, at=(0, 0, h - 0.03), bevel=0.003), m, grain=0)
    for sx in (-1, 1):
        g.add(box(0.03, d, h - 0.03, at=(sx * (w / 2 - 0.015), 0, 0)), m, grain=2)
    g.add(box(w - 0.06, d - 0.05, 0.02, at=(0, 0.02, 0.18)), m, grain=0)
    g.add(box(w - 0.06, 0.015, 0.40, at=(0, d / 2 - 0.01, 0.30)), m, grain=0)
    g.add(box(0.34, 0.24, 0.02, at=(-0.15, -0.02, h), bevel=0.004), M['plastic_dark'])
    g.add(cyl(0.06, 0.015, at=(0.38, 0.12, h), seg=16), M['plastic_white'])
    g.add(tube([(0.38, 0.12, h + 0.01), (0.36, 0.12, h + 0.25), (0.30, 0.08, h + 0.32)], 0.006, sub=4), M['plastic_white'])
    g.add(lathe([(0.0, 0.0), (0.035, -0.01), (0.05, -0.07), (0.0, -0.06)], seg=16), M['plastic_white'], loc=(0.28, 0.06, h + 0.35))
    return g


def chair_white():
    g = Geo()
    shell = M['plastic_white']
    g.add(rbox(0.44, 0.42, 0.04, at=(0, 0, 0.44), r=0.02, seg=3), shell)
    g.add(rbox(0.44, 0.04, 0.34, r=0.02, seg=3, origin='center'), shell, rx=-0.1, loc=(0, 0.20, 0.70))
    for sx in (-0.18, 0.18):
        for sy in (-0.17, 0.17):
            g.add(cyl(0.012, 0.44, at=(sx, sy, 0), seg=8), M['wood_beech'])
    return g


def folding_chair_wood():
    g = Geo()
    b = M['wood_beech']
    for sx in (-0.19, 0.19):
        g.add(sweep([(sx, 0.20, 0.0), (sx, 0.14, 0.86)], rect2d(0.03, 0.02)), b)
        g.add(sweep([(sx, -0.22, 0.0), (sx, 0.10, 0.46)], rect2d(0.03, 0.02)), b)
    for k in range(5):
        g.add(box(0.40, 0.065, 0.016, at=(0, -0.17 + k * 0.075, 0.44), bevel=0.003), b, grain=0)
    for k in range(2):
        g.add(box(0.40, 0.016, 0.06, at=(0, 0.16, 0.66 + k * 0.10), bevel=0.003), b, grain=0)
    return g


def wardrobe(w=0.75, d=0.55, h=1.90):
    """Tall dark-wood cabinet with a plank-style door."""
    g = Geo()
    m = M['wood_walnut']
    g.add(box_ext(-w / 2, -d / 2 + 0.02, 0.06, w / 2, d / 2, h - 0.04, bevel=0.004), m, grain=2)
    g.add(box_ext(-w / 2 - 0.02, -d / 2, h - 0.04, w / 2 + 0.02, d / 2 + 0.01, h, bevel=0.006), m, grain=0)
    g.add(box_ext(-w / 2 + 0.02, -d / 2 + 0.03, 0, w / 2 - 0.02, d / 2 - 0.02, 0.06), m)
    for i in range(6):
        x0 = -w / 2 + 0.03 + i * (w - 0.06) / 6
        g.add(box_ext(x0 + 0.002, -d / 2 + 0.005, 0.08, x0 + (w - 0.06) / 6 - 0.002, -d / 2 + 0.025, h - 0.07, bevel=0.002), m, grain=2)
    g.add(cyl(0.008, 0.10, at=(w / 2 - 0.08, -d / 2, 1.0), seg=8), M['metal_grey'])
    return g


# ============================================================ kitchen
def base_run(L, sink_at=None, hob_at=None, d=0.60, h=0.90, fronts='white_matt'):
    """Kitchen base cabinets with a grey wood worktop, round inset sink and black glass hob."""
    g = Geo()
    g.add(box_ext(-L / 2, -d / 2 + 0.06, 0.0, L / 2, d / 2, 0.10), M['plastic_dark'])
    g.add(box_ext(-L / 2, -d / 2 + 0.03, 0.10, L / 2, d / 2, h - 0.04), M['white_matt'])
    n = max(1, round(L / 0.5))
    dw = L / n
    for i in range(n):
        x0 = -L / 2 + i * dw
        drawers = (i == n - 1)
        if drawers:
            for k, (z0, z1) in enumerate(((0.10, 0.40), (0.42, 0.66), (0.68, h - 0.05))):
                g.add(box_ext(x0 + 0.003, -d / 2 + 0.01, z0, x0 + dw - 0.003, -d / 2 + 0.03, z1, bevel=0.003), M[fronts])
                g.add(cyl(0.006, dw * 0.5, at=(x0 + dw * 0.25, -d / 2 + 0.0, z1 - 0.05), seg=8, axis='X'), M['steel'])
        else:
            g.add(box_ext(x0 + 0.003, -d / 2 + 0.01, 0.10, x0 + dw - 0.003, -d / 2 + 0.03, h - 0.05, bevel=0.003), M[fronts])
            g.add(cyl(0.006, 0.16, at=(x0 + dw - 0.06, -d / 2 + 0.0, h - 0.30), seg=8), M['steel'])
    top = M['worktop_grey']
    tz0, tz1 = h - 0.04, h
    if sink_at is None:
        g.add(box_ext(-L / 2, -d / 2 - 0.01, tz0, L / 2, d / 2, tz1, bevel=0.004), top, grain=0)
    else:
        r = 0.21
        sx = sink_at
        g.add(box_ext(-L / 2, -d / 2 - 0.01, tz0, sx - r, d / 2, tz1, bevel=0.004), top, grain=0)
        g.add(box_ext(sx + r, -d / 2 - 0.01, tz0, L / 2, d / 2, tz1, bevel=0.004), top, grain=0)
        g.add(box_ext(sx - r, -d / 2 - 0.01, tz0, sx + r, -r + 0.02, tz1), top, grain=0)
        g.add(box_ext(sx - r, r + 0.02, tz0, sx + r, d / 2, tz1), top, grain=0)
        g.add(lathe([(0.0, tz1 - 0.17), (r - 0.03, tz1 - 0.17), (r - 0.02, tz1 - 0.02), (r + 0.01, tz1 + 0.002),
                     (r + 0.02, tz1 + 0.002)], seg=48), M['steel'], loc=(sx, 0.02, 0))
        tx, ty = sx, 0.24
        g.add(cyl(0.022, 0.05, at=(tx, ty, tz1), seg=16), M['chrome'])
        g.add(tube([(tx, ty, tz1 + 0.04), (tx, ty, tz1 + 0.22), (tx, ty - 0.10, tz1 + 0.26), (tx, ty - 0.16, tz1 + 0.18)], 0.01, sub=6), M['chrome'])
    if hob_at is not None:
        g.add(box(0.58, 0.50, 0.006, at=(hob_at, 0.0, tz1), bevel=0.003), M['black_glass'])
    return g


def tall_oven(w=0.60, d=0.60, h=2.10):
    g = Geo()
    g.add(box_ext(-w / 2, -d / 2 + 0.02, 0.10, w / 2, d / 2, h, bevel=0.003), M['white_matt'])
    g.add(box_ext(-w / 2 + 0.03, -d / 2 + 0.06, 0, w / 2 - 0.03, d / 2, 0.10), M['plastic_dark'])
    g.add(box_ext(-w / 2 + 0.003, -d / 2, 0.11, w / 2 - 0.003, -d / 2 + 0.02, 0.62, bevel=0.003), M['white_matt'])
    g.add(box_ext(-w / 2 + 0.01, -d / 2 - 0.005, 0.64, w / 2 - 0.01, -d / 2 + 0.02, 1.25, bevel=0.004), M['steel'])
    g.add(box_ext(-w / 2 + 0.05, -d / 2 - 0.008, 0.68, w / 2 - 0.05, -d / 2, 1.08, bevel=0.004), M['black_glass'])
    g.add(cyl(0.01, w - 0.12, at=(-w / 2 + 0.06, -d / 2 - 0.03, 1.13), seg=10, axis='X'), M['steel'])
    for k, x in enumerate((-0.18, 0.18)):
        g.add(cyl(0.018, 0.02, at=(x, -d / 2 - 0.01, 1.19), seg=14, axis='Y'), M['steel'], loc=(0, 0, 0))
    g.add(box_ext(-w / 2 + 0.003, -d / 2, 1.27, w / 2 - 0.003, -d / 2 + 0.02, h - 0.01, bevel=0.003), M['white_matt'])
    g.add(cyl(0.006, 0.16, at=(w / 2 - 0.06, -d / 2 - 0.006, 1.32), seg=8), M['steel'])
    return g


def uppers(L, h=0.72, d=0.34):
    g = Geo()
    g.add(box_ext(-L / 2, -d / 2 + 0.02, 0, L / 2, d / 2, h), M['white_matt'])
    n = max(1, round(L / 0.4))
    dw = L / n
    for i in range(n):
        x0 = -L / 2 + i * dw
        g.add(box_ext(x0 + 0.003, -d / 2, 0.003, x0 + dw - 0.003, -d / 2 + 0.02, h - 0.003, bevel=0.003), M['white_matt'])
        hx = x0 + (dw - 0.05 if i % 2 == 0 else 0.05)
        g.add(cyl(0.006, 0.18, at=(hx, -d / 2 - 0.012, 0.05), seg=8), M['steel'])
    return g


def splashback(L, h=0.62):
    g = Geo()
    g.add(box(L, 0.008, h, at=(0, 0, 0)), M['glass_red'])
    return g


def bell_pendant(drop=0.75):
    g = Geo()
    g.add(cyl(0.04, 0.02, at=(0, 0, -0.02), seg=20), M['brass'])
    g.add(cyl(0.004, drop - 0.22, at=(0, 0, -drop + 0.22), seg=6), M['brass'])
    g.add(lathe([(0.03, -drop + 0.22), (0.05, -drop + 0.19), (0.10, -drop + 0.10), (0.16, -drop + 0.02), (0.17, -drop),
                 (0.165, -drop), (0.155, -drop + 0.02), (0.095, -drop + 0.10), (0.045, -drop + 0.185), (0.026, -drop + 0.215)], seg=48),
          M['bell_glass'])
    g.add(lathe([(0.0, -drop + 0.05), (0.03, -drop + 0.08), (0.03, -drop + 0.12), (0.0, -drop + 0.14)], seg=16), M['bulb'])
    return g


def dish_rack():
    g = Geo()
    w = M['plastic_white']
    for sx in (-0.2, 0.2):
        for sy in (-0.14, 0.14):
            g.add(cyl(0.008, 0.70, at=(sx, sy, 0), seg=8), w)
    g.add(box(0.44, 0.32, 0.02, at=(0, 0, 0.68)), w)
    for k in range(10):
        g.add(box(0.008, 0.30, 0.10, at=(-0.18 + k * 0.04, 0, 0.70)), w)
    for k in range(4):
        g.add(lathe([(0.0, 0.0), (0.10, 0.004), (0.11, 0.02), (0.0, 0.02)], seg=24), M['ceramic_white'], rx=pi / 2,
              loc=(-0.08 + k * 0.05, 0, 0.82))
    return g


# ============================================================ bathroom / wc / hall
def glass_screen(w=0.80, h=1.40):
    g = Geo()
    g.add(box(w, 0.008, h, at=(0, 0, 0)), M['glass_clear'])
    for z in (0.15, h - 0.15):
        g.add(box(0.05, 0.03, 0.06, at=(-w / 2 + 0.03, 0, z)), M['chrome'])
    return g


def basin_wall(w=0.60, d=0.45):
    g = Geo()
    outer = rbox(w, d, 0.15, r=0.02, seg=3)
    g.add(outer, M['enamel'])
    g.add(rbox(w - 0.12, d - 0.14, 0.004, at=(0, -0.02, 0.152), r=0.06, seg=4), M['ceramic_white'])
    g.add(cyl(0.02, 0.10, at=(0, d / 2 - 0.07, 0.15), seg=16), M['chrome'])
    g.add(tube([(0, d / 2 - 0.07, 0.24), (0, d / 2 - 0.16, 0.26), (0, d / 2 - 0.20, 0.22)], 0.01, sub=4), M['chrome'])
    g.add(cyl(0.025, 0.40, at=(0, d / 2 - 0.10, -0.40), seg=16), M['chrome'])
    return g


def mirror_cabinet(w=0.70, h=0.62, d=0.14):
    g = Geo()
    g.add(box(w, d, h, at=(0, 0, 0), bevel=0.004), M['white_matt'])
    for x in (-w / 4, w / 4):
        g.add(box(w / 2 - 0.006, 0.006, h - 0.01, at=(x, -d / 2 - 0.003, 0.005)), M['mirror'])
    g.add(box(w, 0.05, 0.04, at=(0, -d / 2 + 0.02, h)), M['white_matt'])
    g.add(box(w - 0.04, 0.01, 0.015, at=(0, -d / 2 - 0.005, h + 0.012)), M['led'])
    return g


def washer(w=0.60, d=0.58, h=0.85):
    g = Geo()
    g.add(box(w, d, h, at=(0, 0, 0), bevel=0.012), M['appliance_white'])
    g.add(box(w - 0.02, 0.01, 0.12, at=(0, -d / 2 - 0.004, h - 0.13)), M['plastic_grey'])
    g.add(cyl(0.025, 0.02, at=(0.18, -d / 2 - 0.01, h - 0.07), seg=16, axis='Y'), M['plastic_dark'], loc=(0, 0, 0))
    g.add(lathe([(0.0, 0.0), (0.19, 0.0), (0.20, 0.03), (0.15, 0.04), (0.0, 0.045)], seg=40), M['chrome'], rx=pi / 2,
          loc=(0, -d / 2 + 0.005, 0.40))
    g.add(cyl(0.14, 0.012, at=(0, -d / 2 - 0.03, 0.40), seg=36, axis='Y'), M['black_glass'], loc=(0, 0.02, 0))
    return g


def boiler(r=0.22, h=0.80):
    """Wall-hung electric water heater (white cylinder) with pipes below."""
    g = Geo()
    g.add(cyl(r, h, at=(0, 0, 0), seg=40, bevel=0.03, bseg=3), M['appliance_white'])
    g.add(box(0.22, 0.02, 0.06, at=(0, -r + 0.004, h * 0.75), bevel=0.004), M['plastic_grey'])
    for x in (-0.06, 0.06):
        g.add(tube([(x, 0, 0.0), (x, 0, -0.18), (x, 0.05, -0.30)], 0.011, sub=4), M['chrome'])
    return g


def plywood_cabinet(w=0.60, d=0.40, h=0.90):
    g = Geo()
    p = M['plywood']
    g.add(box(w, d, h, at=(0, 0, 0), bevel=0.004), p, grain=2)
    for k in range(5):
        g.add(cyl(0.017, 0.006, at=(-0.20 + k * 0.10, -d / 2 - 0.002, h - 0.15), seg=16, axis='Y'), M['plastic_dark'], loc=(0, 0, 0))
    g.add(box(0.008, 0.004, h - 0.30, at=(0, -d / 2 - 0.002, 0.06)), M['plastic_dark'])
    return g


def toilet_wallhung():
    """Wall-hung pan; origin on the wall, pan faces -Y."""
    g = Geo()
    e = M['enamel']
    pan = lathe([(0.0, 0.0), (0.12, 0.0), (0.17, 0.08), (0.18, 0.19), (0.0, 0.19)], seg=40)
    xform(pan, scale=(1.0, 1.45, 1.0))
    g.add(pan, e, loc=(0, -0.29, 0.21))
    g.add(box(0.30, 0.22, 0.24, at=(0, -0.11, 0.18), bevel=0.05, seg=4), e)
    seat = lathe([(0.10, 0.0), (0.18, 0.0), (0.18, 0.02), (0.10, 0.02)], seg=40)
    xform(seat, scale=(1.0, 1.35, 1.0))
    g.add(seat, M['plastic_white'], loc=(0, -0.30, 0.40))
    lid = cyl(0.18, 0.018, seg=40, bevel=0.008)
    xform(lid, scale=(1.0, 1.32, 1.0))
    g.add(lid, M['plastic_white'], loc=(0, -0.30, 0.42))
    return g


def prewall(w, h=1.15, d=0.20):
    """Tiled installation pre-wall with a chrome flush plate; front at -Y, origin at the wall."""
    g = Geo()
    g.add(box(w, d, h, at=(0, -d / 2, 0)), M['tile_beige'])
    g.add(box(w + 0.01, d + 0.01, 0.03, at=(0, -d / 2, h), bevel=0.004), M['tile_beige'])
    g.add(box(0.24, 0.012, 0.16, at=(0, -d - 0.006, h - 0.30), bevel=0.004), M['chrome'])
    g.add(box(0.10, 0.004, 0.12, at=(-0.055, -d - 0.013, h - 0.28)), M['plastic_dark'])
    g.add(box(0.10, 0.004, 0.12, at=(0.055, -d - 0.013, h - 0.28)), M['plastic_dark'])
    return g


def step_shelf(c=0.36, d=0.36):
    """White cube shelf stepping 1-2-3 high, with an LED strip along the top edges."""
    g = Geo()
    w = M['white_matt']
    t = 0.018
    for col, n in enumerate((1, 2, 3)):
        x0 = -1.5 * c + col * c
        for k in range(n + 1):
            g.add(box_ext(x0, -d / 2, k * c, x0 + c, d / 2, k * c + t), w)
        g.add(box_ext(x0, -d / 2, 0, x0 + t, d / 2, n * c + t), w)
        g.add(box_ext(x0 + c - t, -d / 2, 0, x0 + c, d / 2, n * c + t), w)
        g.add(box_ext(x0, d / 2 - 0.006, 0, x0 + c, d / 2, n * c), w)
        g.add(box_ext(x0, -d / 2 - 0.004, n * c + t - 0.004, x0 + c, -d / 2, n * c + t), M['led'])
    g.add(box(0.20, 0.14, 0.03, at=(-1.5 * c + c / 2, 0, c + t)), M['book_d'])
    g.add(cyl(0.05, 0.08, at=(0.5 * c + c / 2, 0, 3 * c + t), seg=16), M['glass_clear'])
    g.add(lathe([(0.0, 0.0), (0.08, 0.0), (0.09, 0.04), (0.0, 0.04)], seg=24), M['rattan'], loc=(-0.5 * c + c / 2, 0, 2 * c + t))
    return g


def skirt_cabinet(w=1.00, d=0.42, h=0.85):
    """Low cabinet with a wooden top and a gathered fabric skirt."""
    g = Geo()
    g.add(box(w, d, 0.03, at=(0, 0, h - 0.03), bevel=0.004), M['wood_beech'], grain=0)

    def f(u, v):
        x = (u - 0.5) * (w - 0.02)
        return (x, -d / 2 + 0.01 + 0.012 * sin(u * 26 * pi), v * (h - 0.05))
    g.add(grid_surface(f, 120, 2), M['curtain_cream'])
    g.add(box(w - 0.04, d - 0.04, h - 0.04, at=(0, 0.01, 0)), M['white_matt'])
    return g


def round_mirror(r=0.18):
    g = Geo()
    g.add(cyl(r, 0.02, seg=40, axis='Y', bevel=0.006), M['wood_beech'], loc=(0, 0.0, 0))
    g.add(cyl(r - 0.02, 0.004, seg=40, axis='Y'), M['mirror'], loc=(0, -0.012, 0))
    return g
