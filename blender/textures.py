"""Derived textures (tints, tile layouts, rugs, poster, curtain) generated with numpy inside Blender."""
import bpy
import numpy as np
import os
from lib import GEN, acg

RNG = np.random.default_rng(7)


def read(path):
    im = bpy.data.images.load(path, check_existing=False)
    w, h = im.size
    a = np.empty(w * h * 4, dtype=np.float32)
    im.pixels.foreach_get(a)
    bpy.data.images.remove(im)
    return a.reshape(h, w, 4)[:, :, :3].copy()


def write(name, rgb, quality=90):
    path = os.path.join(GEN, name)
    h, w = rgb.shape[:2]
    im = bpy.data.images.new(name, w, h, alpha=False)
    a = np.ones((h, w, 4), dtype=np.float32)
    a[:, :, :3] = np.clip(rgb, 0, 1)
    im.pixels.foreach_set(a.ravel())
    im.filepath_raw = path
    im.file_format = 'JPEG'
    bpy.context.scene.render.image_settings.quality = quality
    im.save()
    bpy.data.images.remove(im)
    return path


def resize(a, w, h):
    ys = (np.arange(h) * a.shape[0] / h).astype(int)
    xs = (np.arange(w) * a.shape[1] / w).astype(int)
    return a[ys][:, xs]


def normal_from_height(hgt, strength=2.0):
    gy, gx = np.gradient(hgt)
    n = np.dstack((-gx * strength, gy * strength, np.ones_like(hgt)))
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return n * 0.5 + 0.5


def tile_layout(base, size_px, cols, rows, grout_px, grout_rgb, tint=(1, 1, 1), jitter=0.04, name='tile'):
    """Build a tiled wall texture: each tile is a random crop of `base`, separated by grout lines."""
    W, Hh = size_px
    out = np.zeros((Hh, W, 3), np.float32)
    hgt = np.zeros((Hh, W), np.float32)
    tw, th = W // cols, Hh // rows
    bh, bw = base.shape[:2]
    for r in range(rows):
        for c in range(cols):
            y0 = RNG.integers(0, max(1, bh - th))
            x0 = RNG.integers(0, max(1, bw - tw))
            crop = base[y0:y0 + th, x0:x0 + tw]
            if crop.shape[0] < th or crop.shape[1] < tw:
                crop = resize(base, tw, th)
            k = 1 + RNG.uniform(-jitter, jitter)
            out[r * th:(r + 1) * th, c * tw:(c + 1) * tw] = crop * np.array(tint) * k
            hgt[r * th:(r + 1) * th, c * tw:(c + 1) * tw] = 1.0
    g = grout_px
    for c in range(cols + 1):
        x = c * tw
        out[:, max(0, x - g // 2):x + (g + 1) // 2] = grout_rgb
        hgt[:, max(0, x - g // 2):x + (g + 1) // 2] = 0.0
    for r in range(rows + 1):
        y = r * th
        out[max(0, y - g // 2):y + (g + 1) // 2, :] = grout_rgb
        hgt[max(0, y - g // 2):y + (g + 1) // 2, :] = 0.0
    # soften the tile edge (rounded bevel)
    from_h = hgt.copy()
    for _ in range(2):
        from_h = (from_h + np.roll(from_h, 1, 0) + np.roll(from_h, -1, 0) + np.roll(from_h, 1, 1) + np.roll(from_h, -1, 1)) / 5
    return out, normal_from_height(from_h, 6.0)


def rug_pattern(w, h, bg, fg, fg2, border, cell=96, name='rug'):
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    out = np.ones((h, w, 3), np.float32) * np.array(bg)
    # diamond lattice
    u = (x % cell) - cell / 2
    v = (y % cell) - cell / 2
    d = np.abs(u) + np.abs(v)
    ring = (d > cell * 0.30) & (d < cell * 0.36)
    core = d < cell * 0.12
    cross = (np.abs(u) < 2.5) & (d < cell * 0.22) | (np.abs(v) < 2.5) & (d < cell * 0.22)
    out[ring] = fg
    out[core] = fg2
    out[cross] = fg
    bw = int(min(w, h) * 0.06)
    edge = (x < bw) | (x > w - bw) | (y < bw) | (y > h - bw)
    inner = (x < bw * 0.5) | (x > w - bw * 0.5) | (y < bw * 0.5) | (y > h - bw * 0.5)
    out[edge] = border
    out[inner] = bg
    # woven noise
    n = RNG.normal(0, 0.035, (h, w, 1)).astype(np.float32)
    weave = 0.03 * np.sin(x * 1.7)[..., None] * np.sin(y * 1.7)[..., None]
    return np.clip(out * (1 + n + weave), 0, 1)


def poster(w=512, h=720):
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    paper = np.array([0.93, 0.87, 0.72])
    out = np.ones((h, w, 3), np.float32) * paper
    out *= (1 + RNG.normal(0, 0.02, (h, w, 1))).astype(np.float32)
    red = np.array([0.66, 0.16, 0.12])
    m = 18
    border = (x < m) | (x > w - m) | (y < m) | (y > h - m)
    out[border] = red
    out[(y > 40) & (y < 112) & (x > 40) & (x < w - 40)] = red
    # illustration: sea, beach, building, sky
    il = (y > 160) & (y < 520) & (x > 40) & (x < w - 40)
    sky = il & (y < 300)
    out[sky] = np.array([0.86, 0.78, 0.55])
    sea = il & (y >= 300) & (y < 400)
    out[sea] = np.array([0.36, 0.55, 0.58])
    beach = il & (y >= 400)
    out[beach] = np.array([0.85, 0.70, 0.45])
    bld = il & (y > 230) & (y < 330) & (x > 120) & (x < 390)
    out[bld] = np.array([0.95, 0.92, 0.82])
    roof = il & (y > 210) & (y <= 230) & (x > 140) & (x < 370)
    out[roof] = np.array([0.6, 0.25, 0.18])
    for k in range(6):
        win = il & (y > 260) & (y < 300) & (x > 140 + k * 40) & (x < 160 + k * 40)
        out[win] = np.array([0.35, 0.45, 0.5])
    # text lines
    for i in range(7):
        yy = 560 + i * 18
        ln = (y > yy) & (y < yy + 6) & (x > 60) & (x < w - 60 - (i % 3) * 40)
        out[ln] = np.array([0.35, 0.28, 0.2])
    return out


def floral(w=1024, h=1024):
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    out = np.ones((h, w, 3), np.float32) * np.array([0.96, 0.95, 0.92])
    cols = [(0.90, 0.60, 0.20), (0.78, 0.25, 0.20), (0.25, 0.37, 0.65), (0.50, 0.72, 0.78), (0.92, 0.82, 0.40), (0.85, 0.55, 0.62)]
    leaf = np.array([0.30, 0.52, 0.30])
    for i in range(140):
        cx, cy = RNG.uniform(0, w), RNG.uniform(0, h)
        s = RNG.uniform(10, 30)
        ang = RNG.uniform(0, np.pi)
        for dx in (-w, 0, w):
            for dy in (-h, 0, h):
                ux, uy = x - cx - dx, y - cy - dy
                lu = ux * np.cos(ang) + uy * np.sin(ang) - s * 1.2
                lv = -ux * np.sin(ang) + uy * np.cos(ang)
                out[(lu / (s * 1.1)) ** 2 + (lv / (s * 0.4)) ** 2 < 1] = leaf
        col = np.array(cols[i % len(cols)])
        for dx in (-w, 0, w):
            for dy in (-h, 0, h):
                ux, uy = x - cx - dx, y - cy - dy
                r = np.sqrt(ux ** 2 + uy ** 2)
                th = np.arctan2(uy, ux)
                petal = r < s * (0.65 + 0.35 * np.abs(np.cos(3 * th)))
                out[petal] = col
                out[r < s * 0.2] = (0.95, 0.80, 0.35)
    return out


WEB = os.path.join(GEN, 'web')
os.makedirs(WEB, exist_ok=True)


def web(path, size, noncolor=False, quality=84):
    """Resized JPEG copy for the web export."""
    out = os.path.join(WEB, os.path.splitext(os.path.basename(path))[0] + f'_{size}.jpg')
    if os.path.exists(out):
        return out
    im = bpy.data.images.load(path, check_existing=False)
    if noncolor:
        im.colorspace_settings.name = 'Non-Color'
    w, h = im.size
    if max(w, h) > size:
        im.scale(size, max(1, int(size * h / w)))
    im.filepath_raw = out
    im.file_format = 'JPEG'
    bpy.context.scene.render.image_settings.quality = quality
    im.save()
    bpy.data.images.remove(im)
    return out


BIG = ('parquet', 'tile_floor', 'tile_bath_floor', 'tile_loggia', 'tile_kitchen', 'tile_bath', 'tile_wc',
       'rug_living', 'rug_hall', 'marble', 'floral', 'poster')
KEEP_ROUGH = ('parquet', 'tile_floor', 'tile_bath_floor', 'tile_loggia', 'marble')


def webify(T):
    for k, d in T.items():
        big = k in BIG
        if d.get('color'):
            d['color'] = web(d['color'], (512 if k.startswith('rug') else 1024) if big else 512)
        if d.get('normal'):
            d['normal'] = web(d['normal'], 512 if big else 256, noncolor=True)
        if d.get('rough'):
            d['rough'] = web(d['rough'], 256, noncolor=True) if k in KEEP_ROUGH else None
    return T


def ensure():
    """Create all derived textures (idempotent). Returns dict of name -> dict(color, rough, normal)."""
    T = {}

    def have(n):
        return os.path.exists(os.path.join(GEN, n))

    # --- parquet: glossy lacquered strip parquet
    src = acg('WoodFloor051')
    if not have('parquet_rough.jpg'):
        r = read(src['rough'])
        write('parquet_rough.jpg', 0.18 + r * 0.32)
    if not have('parquet_color.jpg'):
        c = read(src['color'])
        c = c ** 0.95 * np.array([1.06, 1.0, 0.9])
        write('parquet_color.jpg', c)
    T['parquet'] = dict(color=os.path.join(GEN, 'parquet_color.jpg'), rough=os.path.join(GEN, 'parquet_rough.jpg'), normal=src['normal'])

    # --- tinted woods
    def wood(name, asset, mul, add=0.0, sat=1.0, rough_mul=1.0, rough_add=0.0):
        s = acg(asset)
        if not have(name + '_color.jpg'):
            c = read(s['color'])
            g = c.mean(axis=2, keepdims=True)
            c = g + (c - g) * sat
            write(name + '_color.jpg', c * np.array(mul) + add)
            r = read(s['rough'])
            write(name + '_rough.jpg', r * rough_mul + rough_add)
        T[name] = dict(color=os.path.join(GEN, name + '_color.jpg'), rough=os.path.join(GEN, name + '_rough.jpg'), normal=s['normal'])
    wood('wood_lack', 'Wood049', (1.25, 1.22, 1.15), 0.18, 0.55, 0.9, 0.05)       # white-stained oak (LACK)
    wood('wood_billy', 'Wood049', (0.22, 0.19, 0.17), 0.0, 0.8, 0.8, 0.1)           # black-brown (BILLY)
    wood('wood_pine', 'Wood092', (1.02, 0.98, 0.9), 0.0, 1.0, 0.8, 0.1)             # pine (TARVA / IVAR)
    wood('wood_birch', 'Wood068', (1.05, 1.03, 0.98), 0.03, 0.8, 0.8, 0.1)          # birch (POÄNG, desk)
    wood('wood_oak', 'Wood058', (1.08, 1.02, 0.94), 0.02, 0.95, 0.7, 0.1)           # oak table top
    wood('wood_cherry', 'Wood052', (0.98, 0.86, 0.72), 0.0, 1.05, 0.6, 0.15)        # kitchen fronts
    wood('wood_dark', 'Wood028', (1.1, 1.05, 1.0), 0.0, 1.0, 0.7, 0.1)              # dark cabinet
    wood('wood_skirting', 'Wood028', (1.7, 1.45, 1.2), 0.02, 1.0, 0.7, 0.1)         # brown skirting

    # --- fabrics
    def fabric(name, asset, mul, add=0.0, desat=0.0):
        s = acg(asset)
        if not have(name + '_color.jpg'):
            c = read(s['color'])
            g = c.mean(axis=2, keepdims=True)
            c = c * (1 - desat) + g * desat
            write(name + '_color.jpg', c * np.array(mul) + add)
        T[name] = dict(color=os.path.join(GEN, name + '_color.jpg'), rough=s['rough'], normal=s['normal'])
    fabric('fab_sofa', 'Fabric023', (0.42, 0.48, 0.72))       # FRIHETEN dark blue
    fabric('fab_velvet', 'Fabric036', (0.30, 0.40, 0.95), 0.0, 1.0)
    fabric('fab_grey', 'Fabric030', (0.62, 0.63, 0.66), 0.0, 1.0)
    fabric('fab_charcoal', 'Fabric030', (0.30, 0.31, 0.33), 0.0, 1.0)
    fabric('fab_linen', 'Fabric062', (1.05, 1.0, 0.92), 0.04, 0.6)
    fabric('fab_white', 'Fabric062', (1.12, 1.12, 1.1), 0.08, 1.0)
    fabric('fab_shade', 'Fabric062', (1.05, 0.98, 0.86), 0.05, 0.7)

    # --- marble worktop
    s = acg('Marble014')
    T['marble'] = dict(color=s['color'], rough=s['rough'], normal=s['normal'])

    # --- wall tiles (1 m x 1 m textures)
    marble = read(acg('Marble014')['color'])
    if not have('tile_kitchen_color.jpg'):
        c, n = tile_layout(marble, (1000, 1000), 5, 4, 5, (0.42, 0.20, 0.15), tint=(1.0, 0.90, 0.84))
        write('tile_kitchen_color.jpg', c)
        write('tile_kitchen_normal.jpg', n)
        c, n = tile_layout(marble, (1000, 1000), 5, 4, 4, (0.80, 0.80, 0.80), tint=(0.86, 0.87, 0.90), jitter=0.03)
        g = c.mean(axis=2, keepdims=True)
        write('tile_bath_color.jpg', g * 0.55 + c * 0.45 + 0.03)
        write('tile_bath_normal.jpg', n)
        c, n = tile_layout(marble, (1000, 1000), 5, 4, 4, (0.83, 0.78, 0.68), tint=(1.0, 0.94, 0.80))
        write('tile_wc_color.jpg', c)
        write('tile_wc_normal.jpg', n)
    for k in ('kitchen', 'bath', 'wc'):
        T['tile_' + k] = dict(color=os.path.join(GEN, f'tile_{k}_color.jpg'), normal=os.path.join(GEN, f'tile_{k}_normal.jpg'))
    for k, a in (('tile_floor', 'Tiles141'), ('tile_bath_floor', 'Tiles141'), ('tile_loggia', 'Tiles139')):
        s = acg(a)
        T[k] = dict(color=s['color'], rough=s['rough'], normal=s['normal'])

    # --- rugs, poster, curtain
    if not have('rug_living.jpg'):
        write('rug_living.jpg', rug_pattern(800, 1150, (0.90, 0.88, 0.83), (0.30, 0.42, 0.58), (0.56, 0.66, 0.76), (0.30, 0.42, 0.58), cell=110))
        write('rug_hall.jpg', rug_pattern(420, 1200, (0.86, 0.85, 0.83), (0.40, 0.41, 0.44), (0.62, 0.62, 0.64), (0.40, 0.41, 0.44), cell=84))
        write('poster.jpg', poster())
        write('floral.jpg', floral())
    T['rug_living'] = dict(color=os.path.join(GEN, 'rug_living.jpg'), normal=acg('Fabric030')['normal'])
    T['rug_hall'] = dict(color=os.path.join(GEN, 'rug_hall.jpg'), normal=acg('Fabric030')['normal'])
    T['poster'] = dict(color=os.path.join(GEN, 'poster.jpg'))
    T['floral'] = dict(color=os.path.join(GEN, 'floral.jpg'))
    return webify(T)
