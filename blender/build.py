"""Build one flat in Blender.  Run:  FLAT=<id> blender -b -P blender/build.py   (default FLAT=riverview)
Writes build/<id>/flat.blend and data/<id>.json. The flat itself lives in blender/flats/<id>.py."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy
import bmesh
import json
import math
from math import pi, radians, cos, sin, atan2
from mathutils import Vector, Matrix

import types
import plan as flat
from plan import S, PX0, PY0, H, X, Y, ROOMS, ROOM_ORDER, SLABS, OPENINGS, SPAWNS, room_area, net_area, FLAT
import lib
from lib import (Geo, box, box_ext, cyl, lathe, make, mat, coll, fit_uv, BUILD, MODELS, ROOT, xform)
import textures
import furniture as F
from furniture import M

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'


# ---------------------------------------------------------------- helpers
def rect_m(r):
    """plan px rect -> (xmin, ymin, xmax, ymax) in Blender metres."""
    x0, y0, x1, y1 = r
    return X(x0), Y(y1), X(x1), Y(y0)


def to_px(x, y):
    return x / S + PX0, -y / S + PY0


def room_at_px(px, py, margin=1.5):
    for k in ROOM_ORDER:
        for r in ROOMS[k]['rects']:
            if r[0] - margin <= px <= r[2] + margin and r[1] - margin <= py <= r[3] + margin:
                return k
    return None


def nearest_room_px(px, py):
    best, bd = None, 1e9
    for k in ROOM_ORDER:
        for r in ROOMS[k]['rects']:
            dx = max(r[0] - px, 0, px - r[2])
            dy = max(r[1] - py, 0, py - r[3])
            d = math.hypot(dx, dy)
            if d < bd:
                best, bd = k, d
    return best, bd


def R(room, u, v, i=0):
    """Room-local metres (u east, v south from the inner NW corner) -> Blender (x, y)."""
    r = ROOMS[room]['rects'][i]
    return X(r[0]) + u, Y(r[1]) - v


def P(px, py):
    return X(px), Y(py)


FACING = {'S': 0.0, 'N': pi, 'E': pi / 2, 'W': -pi / 2}


def quad(x0, y0, x1, y1, z, up=True):
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in ((x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z))]
    bm.faces.new(vs if up else list(reversed(vs)))
    return bm


# ---------------------------------------------------------------- materials
T = textures.ensure()


def tm(name, key, tile, **kw):
    return mat(name, tex=T[key], tile=tile, **kw)


M.update({
    'paint': mat('paint', (0.90, 0.885, 0.86), 0.9),
    'paint_ceiling': mat('paint_ceiling', (0.93, 0.93, 0.92), 0.95),
    'facade': mat('facade', (0.78, 0.75, 0.69), 0.95),
    'walltop': mat('walltop', (0.18, 0.18, 0.19), 0.9),
    'concrete': mat('concrete', (0.70, 0.69, 0.66), 0.95),
    'parquet': tm('parquet', 'parquet', 1.15, normal=0.5),
    'tile_floor': tm('tile_floor', 'tile_floor', 1.95, normal=0.5),
    'tile_bath_floor': tm('tile_bath_floor', 'tile_bath_floor', 1.3, normal=0.5),
    'tile_loggia': tm('tile_loggia', 'tile_loggia', 1.9, normal=0.6),
    'tile_kitchen': tm('tile_kitchen', 'tile_kitchen', 1.0, rough=0.22, normal=0.5),
    'tile_bath': tm('tile_bath', 'tile_bath', 1.0, rough=0.18, normal=0.5),
    'tile_wc': tm('tile_wc', 'tile_wc', 1.0, rough=0.22, normal=0.5),
    'tile_band': mat('tile_band', (0.58, 0.38, 0.16), 0.25),
    'wood_skirting': tm('wood_skirting', 'wood_skirting', 0.8),
    'wood_lack': tm('wood_lack', 'wood_lack', 0.9, normal=0.3),
    'wood_billy': tm('wood_billy', 'wood_billy', 0.9, normal=0.3),
    'wood_pine': tm('wood_pine', 'wood_pine', 0.9, normal=0.4),
    'wood_birch': tm('wood_birch', 'wood_birch', 0.9, normal=0.3),
    'wood_oak': tm('wood_oak', 'wood_oak', 0.9, normal=0.4),
    'wood_cherry': tm('wood_cherry', 'wood_cherry', 0.9, normal=0.3),
    'wood_dark': tm('wood_dark', 'wood_dark', 0.9, normal=0.4),
    'wood_black': mat('wood_black', (0.035, 0.035, 0.037), 0.45),
    'bamboo': mat('bamboo', (0.70, 0.52, 0.30), 0.5),
    'rattan': mat('rattan', (0.62, 0.45, 0.26), 0.8),
    'fab_sofa': tm('fab_sofa', 'fab_sofa', 0.35, rough=0.9, normal=0.8),
    'fab_velvet': tm('fab_velvet', 'fab_velvet', 0.35, rough=0.75, normal=0.5),
    'fab_grey': tm('fab_grey', 'fab_grey', 0.35, rough=0.95, normal=0.8),
    'fab_charcoal': tm('fab_charcoal', 'fab_charcoal', 0.35, rough=0.95, normal=0.8),
    'fab_linen': tm('fab_linen', 'fab_linen', 0.35, rough=0.95, normal=0.8),
    'fab_white': tm('fab_white', 'fab_white', 0.35, rough=0.95, normal=0.6),
    'fab_shade': tm('fab_shade', 'fab_shade', 0.3, rough=0.95, normal=0.5, double=True),
    'leather': mat('leather', (0.33, 0.20, 0.12), 0.55),
    'terracotta': mat('terracotta', (0.62, 0.33, 0.20), 0.85),
    'soil': mat('soil', (0.10, 0.07, 0.05), 0.95),
    'white_furn': mat('white_furn', (0.86, 0.855, 0.84), 0.45),
    'white_gloss': mat('white_gloss', (0.88, 0.875, 0.86), 0.22),
    'door_white': mat('door_white', (0.88, 0.875, 0.86), 0.3),
    'door_entry': mat('door_entry', (0.84, 0.86, 0.86), 0.32),
    'pvc_white': mat('pvc_white', (0.90, 0.90, 0.89), 0.3),
    'radiator': mat('radiator', (0.90, 0.90, 0.89), 0.32),
    'plastic_white': mat('plastic_white', (0.88, 0.88, 0.87), 0.35),
    'plastic_gloss': mat('plastic_gloss', (0.90, 0.90, 0.89), 0.18),
    'plastic_grey': mat('plastic_grey', (0.55, 0.56, 0.58), 0.4),
    'plastic_dark': mat('plastic_dark', (0.03, 0.03, 0.035), 0.4),
    'appliance_white': mat('appliance_white', (0.88, 0.885, 0.88), 0.25),
    'enamel': mat('enamel', (0.90, 0.90, 0.89), 0.06, coat=0.0),
    'ceramic_white': mat('ceramic_white', (0.88, 0.87, 0.84), 0.15),
    'metal_black': mat('metal_black', (0.03, 0.03, 0.032), 0.45, 0.6),
    'metal_grey': mat('metal_grey', (0.42, 0.43, 0.45), 0.35, 0.8),
    'metal_white': mat('metal_white', (0.88, 0.88, 0.87), 0.35),
    'chrome': mat('chrome', (0.90, 0.90, 0.90), 0.06, 1.0),
    'steel': mat('steel', (0.75, 0.75, 0.76), 0.25, 1.0),
    'brass': mat('brass', (0.80, 0.58, 0.28), 0.25, 1.0),
    'bronze': mat('bronze', (0.25, 0.20, 0.16), 0.35, 1.0),
    'cast_iron': mat('cast_iron', (0.04, 0.04, 0.04), 0.6, 0.5),
    'black_glass': mat('black_glass', (0.02, 0.02, 0.025), 0.05),
    'screen': mat('screen', (0.01, 0.012, 0.016), 0.08),
    'mirror': mat('mirror', (0.95, 0.95, 0.95), 0.02, 1.0),
    'glass': mat('glass', (0.92, 0.96, 0.98), 0.02, alpha=0.12),
    'glass_clear': mat('glass_clear', (0.92, 0.96, 0.98), 0.05, alpha=0.35),
    'glass_frosted': mat('glass_frosted', (0.93, 0.90, 0.84), 0.5, alpha=0.82),
    'sheer': mat('sheer', (0.86, 0.86, 0.85), 0.95, alpha=0.62, double=True),
    'marble': tm('marble', 'marble', 1.2, rough=0.25, normal=0.3),
    'laminate_red': mat('laminate_red', (0.42, 0.10, 0.06), 0.35),
    'fruit_a': mat('fruit_a', (0.85, 0.55, 0.10), 0.4),
    'fruit_b': mat('fruit_b', (0.55, 0.62, 0.15), 0.4),
    'paper': mat('paper', (0.95, 0.95, 0.94), 0.9),
    'poster': mat('poster', tex=T['poster'], rough=0.8, tile=1.0),
    'rug_living': mat('rug_living', tex=T['rug_living'], rough=0.98, normal=0.6, tile=1.0),
    'rug_hall': mat('rug_hall', tex=T['rug_hall'], rough=0.98, normal=0.6, tile=1.0),
    'coir': mat('coir', (0.55, 0.42, 0.26), 0.98),
    'curtain_floral': mat('curtain_floral', tex=T['floral'], rough=0.85, tile=1.0, double=True),
    # light emitting surfaces (values tuned for the Cycles bake; the web viewer scales them)
    'shade_glow': mat('shade_glow', (0.95, 0.88, 0.76), 0.9, emission=(1.0, 0.82, 0.62), strength=2.0, double=True),
    'paper_glow': mat('paper_glow', (0.96, 0.95, 0.92), 0.9, emission=(1.0, 0.86, 0.68), strength=1.2, double=True),
    'glass_glow': mat('glass_glow', (0.95, 0.93, 0.88), 0.3, emission=(1.0, 0.85, 0.65), strength=3.0, double=True),
    'bulb': mat('bulb', (1.0, 0.95, 0.85), 0.2, emission=(1.0, 0.82, 0.6), strength=12.0),
})
for i, c in enumerate([(0.55, 0.16, 0.12), (0.18, 0.28, 0.40), (0.82, 0.76, 0.62), (0.25, 0.38, 0.28), (0.72, 0.62, 0.48), (0.35, 0.30, 0.38)]):
    M['book_' + 'abcdef'[i]] = mat('book_' + 'abcdef'[i], c, 0.7)

# ---------------------------------------------------------------- materials added for the garden flat
M.update({
    'laminate': tm('laminate', 'laminate', 1.25, normal=0.35),
    'tile_beige': tm('tile_beige', 'tile_beige', 1.0, rough=0.2, normal=0.5),
    'tile_grey_floor': tm('tile_grey_floor', 'tile_grey_floor', 0.9, rough=0.35, normal=0.5),
    'wood_beech': tm('wood_beech', 'wood_beech', 0.9, normal=0.3),
    'wood_spruce': tm('wood_spruce', 'wood_spruce', 0.9, normal=0.35),
    'wood_walnut': tm('wood_walnut', 'wood_walnut', 0.9, normal=0.35),
    'plywood': tm('plywood', 'plywood', 0.9, normal=0.25),
    'worktop_grey': tm('worktop_grey', 'worktop_grey', 1.0, normal=0.25),
    'fab_teal': tm('fab_teal', 'fab_teal', 0.35, rough=0.85, normal=0.8),
    'fab_slate': tm('fab_slate', 'fab_slate', 0.35, rough=0.95, normal=0.8),
    'fab_navy': tm('fab_navy', 'fab_navy', 0.35, rough=0.8, normal=0.5),
    'fab_brown': tm('fab_brown', 'fab_brown', 0.35, rough=0.95, normal=0.8),
    'fab_orange': tm('fab_orange', 'fab_orange', 0.35, rough=0.95, normal=0.7),
    'fab_peach': tm('fab_peach', 'fab_peach', 0.35, rough=0.95, normal=0.7),
    'fab_blue': tm('fab_blue', 'fab_blue', 0.35, rough=0.85, normal=0.5),
    'fab_rugdark': tm('fab_rugdark', 'fab_rugdark', 0.3, rough=0.98, normal=0.9),
    'fab_olive': mat('fab_olive', (0.55, 0.58, 0.22), 0.95),
    'quilt': mat('quilt', tex=T['floral'], rough=0.9, tile=0.9),
    'curtain_cream': mat('curtain_cream', (0.86, 0.82, 0.74), 0.95, double=True),
    'macrame': mat('macrame', (0.88, 0.84, 0.76), 0.98),
    'white_matt': mat('white_matt', (0.88, 0.875, 0.865), 0.5),
    'frame_grey': mat('frame_grey', (0.78, 0.78, 0.77), 0.35, 0.3),
    'glass_red': mat('glass_red', (0.36, 0.02, 0.04), 0.03, spec=0.8),
    'bowl_blue': mat('bowl_blue', (0.05, 0.12, 0.30), 0.2),
    'crystal': mat('crystal', (0.96, 0.97, 1.0), 0.02, alpha=0.5),
    'decal_black': mat('decal_black', (0.02, 0.02, 0.022), 0.6),
    'mosaic': mat('mosaic', (0.35, 0.62, 0.62), 0.12),
    'rug_white': mat('rug_white', (0.86, 0.84, 0.78), 0.97),
    'led': mat('led', (1.0, 0.97, 0.92), 0.3, emission=(1.0, 0.95, 0.88), strength=6.0),
    'bell_glass': mat('bell_glass', (0.90, 0.86, 0.78), 0.35, emission=(1.0, 0.85, 0.65), strength=1.5, double=True),
    'canvas_dream': mat('canvas_dream', tex=T['dreamcatcher'], rough=0.85, tile=1.0),
    'art_lemons': mat('art_lemons', tex=T['lemons'], rough=0.6, tile=1.0),
    'art_lemons_blue': mat('art_lemons_blue', tex=T['lemons_blue'], rough=0.6, tile=1.0),
    'art_arch': mat('art_arch', tex=T['art_arch'], rough=0.6, tile=1.0),
    'sign_ocean': mat('sign_ocean', tex=T['sign_ocean'], rough=0.8, tile=1.0),
})
M['door_frame'] = M['door_white']
M['door_leaf'] = M['door_white']
for _k, _v in getattr(flat, 'MAT_ALIASES', {}).items():     # per-flat finishes (e.g. beech doors in grey steel frames)
    M[_k] = M[_v]


# ---------------------------------------------------------------- walls (boolean union minus openings)
def build_walls():
    tmp = coll('_tmp_union')
    cut = coll('_tmp_cut')
    objs = []
    for i, r in enumerate(SLABS):
        xa, ya, xb, yb = rect_m(r)
        bm = box_ext(xa, ya, 0, xb, yb, H)
        me = bpy.data.meshes.new(f'_slab{i}')
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new(f'_slab{i}', me)
        (coll('_tmp_base') if i == 0 else tmp).objects.link(o)
        objs.append(o)
    for op in OPENINGS:
        xa, ya, xb, yb = rect_m(op['rect'])
        z0, z1 = op['z']
        bm = box_ext(xa, ya, z0 if z0 > 0 else -0.1, xb, yb, z1)
        me = bpy.data.meshes.new('_cut_' + op['id'])
        bm.to_mesh(me)
        bm.free()
        cut.objects.link(bpy.data.objects.new('_cut_' + op['id'], me))
    base = objs[0]
    m1 = base.modifiers.new('u', 'BOOLEAN')
    m1.operation, m1.operand_type, m1.collection, m1.solver = 'UNION', 'COLLECTION', tmp, 'EXACT'
    m2 = base.modifiers.new('d', 'BOOLEAN')
    m2.operation, m2.operand_type, m2.collection, m2.solver = 'DIFFERENCE', 'COLLECTION', cut, 'EXACT'
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    bm = bmesh.new()
    bm.from_object(base, dg)
    for c in ('_tmp_union', '_tmp_cut', '_tmp_base'):
        cc = bpy.data.collections[c]
        for o in list(cc.objects):
            me = o.data
            bpy.data.objects.remove(o)
            bpy.data.meshes.remove(me)
        bpy.data.collections.remove(cc)
        lib.COLLS.pop(c, None)
    bmesh.ops.dissolve_limit(bm, angle_limit=radians(0.5), verts=bm.verts[:], edges=bm.edges[:])
    groups = {}
    for f in bm.faces:
        c = f.calc_center_median()
        n = f.normal
        if n.z < -0.9 and c.z < 0.01:
            key = None
        elif n.z > 0.9 and c.z > H - 0.01:
            key = 'top'
        else:
            p = c + n * 0.03
            px, py = to_px(p.x, p.y)
            key = room_at_px(px, py, 0.5)
            if key is None:
                k2, d = nearest_room_px(px, py)
                key = k2 if d < 9 else 'ext'
        groups.setdefault(key, []).append(f.index)
    out = {}
    for key, idx in groups.items():
        if key is None:
            continue
        b2 = bm.copy()
        b2.faces.ensure_lookup_table()
        keep = set(idx)
        bmesh.ops.delete(b2, geom=[f for f in b2.faces if f.index not in keep], context='FACES')
        g = Geo()
        m = {'top': M['walltop'], 'ext': M['facade']}.get(key, M['paint'] if key not in flat.OUTDOOR else M['facade'])
        g.add(b2, m, jitter=False)
        out[key] = make('walls_' + key, g, collection='arch', room=(key if key in ROOMS else None), smooth=None,
                        lightmap=key in ROOMS, props={'kind': 'walltop' if key == 'top' else 'wall'})
    bm.free()
    return out


# ---------------------------------------------------------------- floors, ceilings, thresholds
def build_floors():
    for key, room in ROOMS.items():
        g = Geo()
        for r in room['rects']:
            xa, ya, xb, yb = rect_m(r)
            g.add(quad(xa, ya, xb, yb, 0.0), M[room['floor']], jitter=False)
        make('floor_' + key, g, collection='arch', room=key, smooth=None, props={'kind': 'floor'})
        if key not in flat.OUTDOOR:
            g = Geo()
            for r in room['rects']:
                xa, ya, xb, yb = rect_m(r)
                g.add(quad(xa, ya, xb, yb, H, up=False), M['paint_ceiling'], jitter=False)
            make('ceiling_' + key, g, collection='arch', room=key, smooth=None, props={'kind': 'ceiling'})
    if hasattr(flat, 'extra_arch'):
        flat.extra_arch(types.SimpleNamespace(**globals()))
    # thresholds in door gaps
    for op in OPENINGS:
        if op['z'][0] > 0 or op['kind'] in ('balcony',):
            continue
        a0, a1 = (op['rect'][0], op['rect'][2]) if op['axis'] == 'x' else (op['rect'][1], op['rect'][3])
        w0, w1 = op['wall']
        r = (a0, w0, a1, w1) if op['axis'] == 'x' else (w0, a0, w1, a1)
        xa, ya, xb, yb = rect_m(r)
        sides = side_rooms(op)
        floors = [ROOMS[s]['floor'] if s in ROOMS else 'tile_floor' for s in sides]
        g = Geo()
        if op['id'] == 'door_front':
            g.add(box_ext(xa, ya, 0, xb, yb, 0.012, bevel=0.003), M['concrete'])
        elif floors[0] == floors[1]:
            g.add(quad(xa, ya, xb, yb, 0.0), M[floors[0]], jitter=False)
        else:
            g.add(box_ext(xa, ya - 0.01, 0, xb, yb + 0.01, 0.008, bevel=0.003) if op['axis'] == 'x'
                  else box_ext(xa - 0.01, ya, 0, xb + 0.01, yb, 0.008, bevel=0.003), M['wood_oak'], grain=(0 if op['axis'] == 'x' else 1))
        make('threshold_' + op['id'], g, collection='arch', room=sides[0] if sides[0] in ROOMS else sides[1], smooth=None)


def side_rooms(op):
    """Rooms on the two sides of an opening: (min side, max side) along the wall normal."""
    if op['axis'] == 'x':
        cx = (op['rect'][0] + op['rect'][2]) / 2
        w0, w1 = op['wall']
        return (room_at_px(cx, w0 - 4) or 'outside', room_at_px(cx, w1 + 4) or 'outside')
    cy = (op['rect'][1] + op['rect'][3]) / 2
    w0, w1 = op['wall']
    return (room_at_px(w0 - 4, cy) or 'outside', room_at_px(w1 + 4, cy) or 'outside')


# ---------------------------------------------------------------- wall runs (for skirting / tiles)
def wall_runs(key, rect):
    """For each edge of a room rect yield (edge, a0, a1, cap) segments in px; cap = sill height or None.
    edge: 'N','S' (along x) or 'W','E' (along y)."""
    x0, y0, x1, y1 = rect
    edges = {'N': ('x', y0, x0, x1), 'S': ('x', y1, x0, x1), 'W': ('y', x0, y0, y1), 'E': ('y', x1, y0, y1)}
    for e, (ax, pos, a, b) in edges.items():
        cuts = []
        for op in OPENINGS:
            if op['axis'] != ax:
                continue
            w0, w1 = op['wall']
            if not (abs(w0 - pos) <= 6 or abs(w1 - pos) <= 6):
                continue
            c0, c1 = (op['rect'][0], op['rect'][2]) if ax == 'x' else (op['rect'][1], op['rect'][3])
            if c1 <= a or c0 >= b:
                continue
            cuts.append((max(a, c0), min(b, c1), op['z'][0] if op['z'][0] > 0 else None))
        # the hall: drop edges that are open to the other hall rectangle
        segs = []
        cur = a
        for c0, c1, cap in sorted(cuts):
            if c0 > cur:
                segs.append((cur, c0, None))
            if cap is not None:
                segs.append((c0, c1, cap))
            cur = max(cur, c1)
        if cur < b:
            segs.append((cur, b, None))
        for s in segs:
            yield (e,) + s


def open_spans(key, e, rect):
    """Spans (a0, a1) of edge `e` of `rect` that touch another rectangle of the same room (no wall there)."""
    x0, y0, x1, y1 = rect
    out = []
    for o in ROOMS[key]['rects']:
        if o == rect:
            continue
        ox0, oy0, ox1, oy1 = o
        if e == 'N' and abs(oy1 - y0) <= 1:
            out.append((max(x0, ox0), min(x1, ox1)))
        elif e == 'S' and abs(oy0 - y1) <= 1:
            out.append((max(x0, ox0), min(x1, ox1)))
        elif e == 'W' and abs(ox1 - x0) <= 1:
            out.append((max(y0, oy0), min(y1, oy1)))
        elif e == 'E' and abs(ox0 - x1) <= 1:
            out.append((max(y0, oy0), min(y1, oy1)))
    return [sp for sp in out if sp[1] > sp[0]]


def minus_spans(a0, a1, spans):
    segs = [(a0, a1)]
    for c0, c1 in spans:
        nxt = []
        for p, q in segs:
            if c1 <= p or c0 >= q:
                nxt.append((p, q))
                continue
            if c0 > p:
                nxt.append((p, c0))
            if c1 < q:
                nxt.append((c1, q))
        segs = nxt
    return segs


def cladding(key, height, matname, thick=0.008, skip=(), band=None, kind='tile'):
    g = Geo()
    for rect in ROOMS[key]['rects']:
        x0, y0, x1, y1 = rect
        for e, a0, a1, cap in wall_runs(key, rect):
            if e in skip:
                continue
            for a0, a1 in minus_spans(a0, a1, open_spans(key, e, rect)):
                clad_piece(g, key, rect, e, a0, a1, cap, height, matname, thick, band)
    if g.f:
        make(f'{kind}_{key}', g, collection='arch', room=key, smooth=None)


def clad_piece(g, key, rect, e, a0, a1, cap, height, matname, thick, band):
    """One tile / skirting slab along edge `e` of `rect`, from a0 to a1 (plan units)."""
    x0, y0, x1, y1 = rect
    top = height if cap is None else min(height, cap)

    def slab(z0, z1, extra=0.0):
        t = thick + extra
        if e == 'N':
            return box_ext(X(a0), Y(y0) - t, z0, X(a1), Y(y0), z1)
        if e == 'S':
            return box_ext(X(a0), Y(y1), z0, X(a1), Y(y1) + t, z1)
        if e == 'W':
            return box_ext(X(x0), Y(a1), z0, X(x0) + t, Y(a0), z1)
        return box_ext(X(x1) - t, Y(a1), z0, X(x1), Y(a0), z1)
    g.add(slab(0, top), M[matname])
    if band and cap is None:
        g.add(slab(band[0], band[1], 0.003), M['tile_band'])


# ---------------------------------------------------------------- doors and frames
def opening_geom(op):
    if op['axis'] == 'x':
        a0, a1 = X(op['rect'][0]), X(op['rect'][2])
        w0, w1 = Y(op['wall'][1]), Y(op['wall'][0])     # Blender y range of the wall (min, max)
    else:
        a0, a1 = Y(op['rect'][3]), Y(op['rect'][1])     # Blender y (min, max) along the wall
        w0, w1 = X(op['wall'][0]), X(op['wall'][1])
    return a0, a1, w0, w1


def to_world(op, a, w):
    return (a, w) if op['axis'] == 'x' else (w, a)


def door_frame(op, room_key):
    a0, a1, w0, w1 = opening_geom(op)
    top = op['z'][1]
    j, prot, arch_w, arch_t = 0.025, 0.012, 0.065, 0.014
    g = Geo()
    fm = M['door_frame'] if op['id'] != 'door_front' else M['door_entry']

    def bx(aa0, aa1, ww0, ww1, z0, z1, m, bev=0.002):
        (xa, ya), (xb, yb) = to_world(op, aa0, ww0), to_world(op, aa1, ww1)
        g.add(box_ext(min(xa, xb), min(ya, yb), z0, max(xa, xb), max(ya, yb), z1, bevel=bev), m)
    # jamb lining
    bx(a0, a0 + j, w0 - prot, w1 + prot, 0, top - j, fm)
    bx(a1 - j, a1, w0 - prot, w1 + prot, 0, top - j, fm)
    bx(a0, a1, w0 - prot, w1 + prot, top - j, top, fm)
    # architraves on both faces (mitre-free butt joints, no overlapping faces)
    for ww0, ww1 in ((w0 - prot - arch_t, w0 - prot), (w1 + prot, w1 + prot + arch_t)):
        bx(a0 - arch_w, a0 + 0.004, ww0, ww1, 0, top - 0.004, fm, 0.003)
        bx(a1 - 0.004, a1 + arch_w, ww0, ww1, 0, top - 0.004, fm, 0.003)
        bx(a0 - arch_w, a1 + arch_w, ww0, ww1, top - 0.004, top + arch_w, fm, 0.003)
    # light switch next to the latch side, on both faces of the wall
    if op['kind'] == 'door' and op['id'] not in ('door_bed_liv',):
        la = (a1 + arch_w + 0.10) if op.get('hinge') == 'a0' else (a0 - arch_w - 0.10)
        if op['axis'] == 'y':
            la = (a0 - arch_w - 0.10) if op.get('hinge') == 'a0' else (a1 + arch_w + 0.10)
        for ww0, ww1 in ((w0 - 0.012, w0), (w1, w1 + 0.012)):
            bx(la - 0.04, la + 0.04, ww0, ww1, 1.03, 1.11, M['plastic_white'], 0.004)
            mid = (ww0 + ww1) / 2 + (0.004 if ww0 >= w1 else -0.004)
            bx(la - 0.022, la + 0.022, min(mid, (ww0 + ww1) / 2), max(mid, (ww0 + ww1) / 2), 1.045, 1.095, M['plastic_white'], 0.003)
    make('frame_' + op['id'], g, collection='arch', room=room_key)
    if op['kind'] == 'arch':
        return
    # leaf
    width = (a1 - a0) - 2 * j - 0.006
    t = 0.06 if op['leaf'] == 'entry' else 0.04
    if op['leaf'] == 'entry':
        leaf = F.entry_door_leaf(width, h=top - j - 0.01, t=t)
    else:
        leaf = F.interior_leaf(width, kind=op['leaf'], h=top - j - 0.012, t=t)
    sides = side_rooms(op)
    s_sign = -1 if sides[0] == op['swing'] else 1          # +1: swing toward larger plan coordinate
    # world vectors
    ax = Vector((1, 0)) if op['axis'] == 'x' else Vector((0, -1))
    sv = (Vector((0, -1)) if op['axis'] == 'x' else Vector((1, 0))) * s_sign
    if op['hinge'] == 'a0':
        ha = (X(op['rect'][0]) if op['axis'] == 'x' else Y(op['rect'][1]))
        closed = ax
        ha = ha + (j + 0.003) * (1 if op['axis'] == 'x' else -1)
    else:
        ha = (X(op['rect'][2]) if op['axis'] == 'x' else Y(op['rect'][3]))
        closed = -ax
        ha = ha - (j + 0.003) * (1 if op['axis'] == 'x' else -1)
    wc = (w0 + w1) / 2
    wt = (w1 - w0)
    face = wc + (wt / 2 - t / 2) * (sv.y if op['axis'] == 'x' else sv.x)
    hx, hy = (ha, face) if op['axis'] == 'x' else (face, ha)
    th = radians(op.get('angle', 0))
    d = closed * cos(th) + sv * sin(th)
    rz = atan2(d.y, d.x)
    make('leaf_' + op['id'], leaf, loc=(hx, hy, 0.008), rz=rz, collection='arch', room=op['swing'],
         props={'kind': 'door'})


# ---------------------------------------------------------------- windows
def window(op, room_key):
    """PVC tilt & turn window / balcony door with sill boards and an exterior roller shutter."""
    a0, a1, w0, w1 = opening_geom(op)
    z0, z1 = op['z']
    inside = room_key
    # which side of the wall is outside (Blender y)
    sides = side_rooms(op)
    out_is_min = sides[1] == inside      # plan min side (north for x walls) is outside
    yo, yi = (w1, w0) if out_is_min else (w0, w1)        # outer face y, inner face y (Blender)
    sgn_in = 1 if yi > yo else -1
    fy = yo + (yi - yo) * 0.45                         # frame plane
    fd = 0.07
    g = Geo()
    pvc = M['pvc_white']
    fw = 0.065

    def b(x0, x1, zz0, zz1, ya, yb, m, bev=0.003):
        g.add(box_ext(x0, min(ya, yb), zz0, x1, max(ya, yb), zz1, bevel=bev), m)
    yA, yB = fy - fd / 2, fy + fd / 2
    b(a0, a1, z0, z0 + fw, yA, yB, pvc)
    b(a0, a1, z1 - fw, z1, yA, yB, pvc)
    b(a0, a0 + fw, z0 + fw, z1 - fw, yA, yB, pvc)
    b(a1 - fw, a1, z0 + fw, z1 - fw, yA, yB, pvc)
    if op['kind'] == 'balcony':
        panes = [(a0 + fw, a1 - fw)]
    else:
        n = op['panes']
        iw = (a1 - a0 - 2 * fw - (n - 1) * 0.07) / n
        panes = []
        for i in range(n):
            pa = a0 + fw + i * (iw + 0.07)
            panes.append((pa, pa + iw))
            if i < n - 1:
                b(pa + iw, pa + iw + 0.07, z0 + fw, z1 - fw, yA, yB, pvc)
    sw = 0.055
    if op['kind'] == 'balcony':
        balcony_leaf(op, panes[0], z0 + fw, z1 - fw, fy, fd, sgn_in, room_key)
        panes = []
    for i, (pa, pb) in enumerate(panes):
        za, zb = z0 + fw, z1 - fw
        pa, pb = pa + 0.002, pb - 0.002
        ys0, ys1 = fy - fd / 2 - 0.004 * sgn_in, fy + fd / 2 + 0.01 * sgn_in
        b(pa, pb, za, za + sw, ys0, ys1, pvc)
        b(pa, pb, zb - sw, zb, ys0, ys1, pvc)
        b(pa, pa + sw, za + sw, zb - sw, ys0, ys1, pvc)
        b(pb - sw, pb, za + sw, zb - sw, ys0, ys1, pvc)
        g.add(box_ext(pa + sw, fy - 0.004, za + sw, pb - sw, fy + 0.004, zb - sw), M['glass'])
        # handle on the inner face
        hx = pb - 0.03 if (i % 2 == 0) else pa + 0.03
        hy = fy + (fd / 2 + 0.012) * sgn_in
        g.add(box_ext(hx - 0.012, min(hy, hy + 0.012 * sgn_in), (za + zb) / 2 - 0.035, hx + 0.012,
                      max(hy, hy + 0.012 * sgn_in), (za + zb) / 2 + 0.035, bevel=0.004), pvc)
        g.add(box_ext(hx - 0.01, min(hy, hy + 0.03 * sgn_in), (za + zb) / 2 - 0.12, hx + 0.01,
                      max(hy, hy + 0.03 * sgn_in) , (za + zb) / 2 + 0.0, bevel=0.005), pvc)
    if op['kind'] == 'window':
        # interior sill board and exterior metal sill
        yi2 = yi + 0.03 * sgn_in
        b(a0 - 0.04, a1 + 0.04, z0 - 0.025, z0, min(fy, yi2), max(fy, yi2), M['white_gloss'] if room_key not in flat.SILL_TILE_ROOMS else M[flat.SILL_TILE_MAT if hasattr(flat, 'SILL_TILE_MAT') else 'tile_kitchen'])
        yo2 = yo - 0.05 * sgn_in
        b(a0 - 0.02, a1 + 0.02, z0 - 0.04, z0 - 0.01, min(fy, yo2), max(fy, yo2), M['metal_grey'])
    # roller shutter box and partly lowered slats on the outside
    sh = 0.17
    yo3 = yo - 0.19 * sgn_in
    b(a0 - 0.03, a1 + 0.03, z1, z1 + sh, min(yo, yo3), max(yo, yo3), M['plastic_grey'])
    for k in range(4):
        zz = z1 - 0.03 - k * 0.04
        b(a0 + 0.01, a1 - 0.01, zz - 0.035, zz, min(yo - 0.06 * sgn_in, yo - 0.075 * sgn_in), max(yo - 0.06 * sgn_in, yo - 0.075 * sgn_in), M['plastic_grey'], 0.004)
    ob = make('window_' + op['id'], g, collection='arch', room=room_key, props={'kind': 'window'})
    return ob


def balcony_leaf(op, pane, za, zb, fy, fd, sgn_in, room_key):
    """Glazed balcony door sash as its own object, opened into the room."""
    pa, pb = pane
    L = (pb - pa) - 0.004
    sw = 0.055
    th = fd + 0.014
    g = Geo()
    pvc = M['pvc_white']
    g.add(box_ext(0, -th / 2, 0, L, th / 2, sw, bevel=0.003), pvc)
    g.add(box_ext(0, -th / 2, zb - za - sw, L, th / 2, zb - za, bevel=0.003), pvc)
    g.add(box_ext(0, -th / 2, sw, sw, th / 2, zb - za - sw, bevel=0.003), pvc)
    g.add(box_ext(L - sw, -th / 2, sw, L, th / 2, zb - za - sw, bevel=0.003), pvc)
    g.add(box_ext(sw, -0.004, sw, L - sw, 0.004, zb - za - sw), M['glass'])
    for side in (-1, 1):
        g.add(box_ext(L - 0.045, side * th / 2, (zb - za) * 0.47, L - 0.02, side * (th / 2 + 0.012), (zb - za) * 0.47 + 0.07, bevel=0.004), pvc)
        g.add(box_ext(L - 0.043, side * (th / 2 + 0.008), (zb - za) * 0.47 - 0.10, L - 0.022, side * (th / 2 + 0.03), (zb - za) * 0.47 + 0.01, bevel=0.005), pvc)
    # hinge on the a1 (east) end; the leaf runs back along -X when closed and swings into the room
    hx = pb
    hy = fy + (fd / 2) * sgn_in
    ang = radians(op.get('angle', 0))
    closed = Vector((-1, 0))
    sv = Vector((0, sgn_in))
    d = closed * cos(ang) + sv * sin(ang)
    make('leaf_' + op['id'], g, loc=(hx, hy, za), rz=atan2(d.y, d.x), collection='arch', room=room_key,
         props={'kind': 'door'})


# ---------------------------------------------------------------- imported CC0 models (Poly Haven)
def import_model(folder, name, room, loc, rz=0.0, height=None, scale=None, lightmap=False, keep=None, drop=None):
    path = None
    d = os.path.join(MODELS, folder)
    for fn in os.listdir(d):
        if fn.endswith('.gltf') or fn.endswith('.glb'):
            path = os.path.join(d, fn)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == 'MESH']
    unwanted = [o for o in meshes if (keep and not any(o.name.split('.')[0].endswith(k) for k in keep)) or (drop and any(k in o.name for k in drop))]
    for o in unwanted:
        meshes.remove(o)
        bpy.data.objects.remove(o)
        new.remove(o)
    bpy.context.view_layer.update()
    mws = {o.name: o.matrix_world.copy() for o in meshes}
    for o in meshes:
        if o.data.users > 1:
            o.data = o.data.copy()
    for o in meshes:
        o.parent = None
    for o in meshes:
        o.data.transform(mws[o.name])
        o.matrix_world = Matrix.Identity(4)
    for o in new:
        if o.type != 'MESH':
            bpy.data.objects.remove(o)
    if len(meshes) > 1:
        with bpy.context.temp_override(active_object=meshes[0], object=meshes[0], selected_objects=meshes,
                                       selected_editable_objects=meshes):
            bpy.ops.object.join()
    ob = meshes[0]
    me = ob.data
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    zs = [v.co.z for v in me.vertices]
    k = scale or (height / (max(zs) - min(zs)) if height else 1.0)
    me.transform(Matrix.Diagonal((k, k, k, 1)) @ Matrix.Translation((-(min(xs) + max(xs)) / 2, -(min(ys) + max(ys)) / 2, -min(zs))))
    for c in ob.users_collection:
        c.objects.unlink(ob)
    coll('decor').objects.link(ob)
    ob.name = name
    shrink_images(ob)
    ob.location = loc
    ob.rotation_euler = (0, 0, rz)
    ob['room'] = room
    ob['lightmap'] = lightmap
    ob['kind'] = 'decor'
    return ob


def shrink_images(ob):
    """Swap the imported model's 1k textures for 512 px (colour) / 256 px (data) copies."""
    for m in ob.data.materials:
        if not m or not m.node_tree:
            continue
        for n in m.node_tree.nodes:
            if n.type != 'TEX_IMAGE' or not n.image or not n.image.filepath:
                continue
            src = bpy.path.abspath(n.image.filepath)
            if '_web' in src or not os.path.exists(src):
                continue
            data = n.image.colorspace_settings.name != 'sRGB'
            size = 256 if data else 512
            if src.lower().endswith('.png'):
                out = os.path.join(lib.GEN, 'web', os.path.splitext(os.path.basename(src))[0] + f'_web{size}.png')
                if not os.path.exists(out):
                    im = bpy.data.images.load(src, check_existing=False)
                    w, h = im.size
                    if max(w, h) > size:
                        im.scale(size, max(1, int(size * h / w)))
                    im.filepath_raw = out
                    im.file_format = 'PNG'
                    im.save()
                    bpy.data.images.remove(im)
            else:
                out = textures.web(src, size, noncolor=data, quality=80)
            cs = n.image.colorspace_settings.name
            n.image = bpy.data.images.load(out, check_existing=True)
            n.image.colorspace_settings.name = cs


# ---------------------------------------------------------------- placement
def place(builder_geo, name, room, u, v, facing='S', z=0.0, solid=False, rz=None, i=0, props=None, lightmap=True):
    x, y = R(room, u, v, i)
    ang = FACING[facing] if rz is None else rz
    return make(name, builder_geo, loc=(x, y, z), rz=ang, room=room, solid=solid, props=props, lightmap=lightmap)


def place_px(builder_geo, name, room, px, py, facing='S', z=0.0, solid=False, props=None):
    x, y = P(px, py)
    return make(name, builder_geo, loc=(x, y, z), rz=FACING[facing], room=room, solid=solid, props=props)


# ---------------------------------------------------------------- lights, world, render settings
def lighting():
    world = bpy.data.worlds.new('World')
    scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    bg = nt.nodes['Background']
    sky = nt.nodes.new('ShaderNodeTexSky')
    sky.sky_type = 'NISHITA'
    sky.sun_disc = False
    sky.sun_elevation = radians(26)
    sky.sun_rotation = radians(200)
    sky.altitude = 120
    sky.air_density = 1.2
    sky.dust_density = 1.6
    nt.links.new(sky.outputs['Color'], bg.inputs['Color'])
    bg.inputs['Strength'].default_value = 1.0
    # sun matching the sky
    sun = bpy.data.lights.new('Sun', 'SUN')
    sun.energy = 45.0
    sun.angle = radians(0.8)
    sun.color = (1.0, 0.86, 0.70)
    so = bpy.data.objects.new('Sun', sun)
    coll('lights').objects.link(so)
    # direction: from plan-north (+Y) slightly from the east, 24 deg above the horizon
    sun.energy = flat.SUN['energy']
    el, az = radians(flat.SUN['elevation']), radians(flat.SUN['azimuth'])
    d = Vector((sin(az) * cos(el), cos(az) * cos(el), sin(el)))   # vector pointing TO the sun
    so.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    # ceiling fill lights per room (soft area lights)
    fills = flat.FILLS
    for key, lst in fills.items():
        for i, (px, py, sx, sy, w) in enumerate(lst):
            l = bpy.data.lights.new(f'fill_{key}_{i}', 'AREA')
            l.shape = 'RECTANGLE'
            l.size, l.size_y = sx, sy
            l.energy = w
            l.color = (1.0, 0.90, 0.78)
            o = bpy.data.objects.new(f'fill_{key}_{i}', l)
            o.location = (X(px), Y(py), H - 0.02)
            coll('lights').objects.link(o)


def render_settings():
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 64
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = 'OPENIMAGEDENOISE'
    scene.cycles.max_bounces = 8
    scene.cycles.diffuse_bounces = 4
    scene.cycles.glossy_bounces = 2
    scene.cycles.transparent_max_bounces = 8
    scene.cycles.light_sampling_threshold = 0.01
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.view_settings.exposure = 0.6
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 800
    scene.cycles.use_adaptive_sampling = True


# ---------------------------------------------------------------- scene description for the web viewer
def write_scene_json():
    rooms = []
    for k in ROOM_ORDER:
        r = ROOMS[k]
        rooms.append(dict(id=k, name=r['name'], hu=r['hu'], area=round(room_area(k), 1),
                          rects=[[X(q[0]), -Y(q[1]), X(q[2]), -Y(q[3])] for q in r['rects']],
                          spawn=[X(SPAWNS[k][0]), -Y(SPAWNS[k][1]), SPAWNS[k][2]]))
        if k in flat.OUTDOOR:
            rooms[-1]['outdoor'] = True
    # wall colliders (doors are passable, windows are not)
    cols = []
    for (x0, y0, x1, y1) in SLABS:
        horiz = (x1 - x0) >= (y1 - y0)
        segs = [(x0, x1) if horiz else (y0, y1)]
        for op in OPENINGS:
            if op['z'][0] > 0 or (op['kind'] in ('door', 'balcony') and op.get('angle', 0) == 0):
                continue
            r = op['rect']
            if horiz and op['axis'] == 'x' and r[1] < y1 and r[3] > y0:
                c0, c1 = r[0], r[2]
            elif not horiz and op['axis'] == 'y' and r[0] < x1 and r[2] > x0:
                c0, c1 = r[1], r[3]
            else:
                continue
            nxt = []
            for a, b in segs:
                if c1 <= a or c0 >= b:
                    nxt.append((a, b))
                else:
                    if c0 > a:
                        nxt.append((a, c0))
                    if c1 < b:
                        nxt.append((c1, b))
            segs = nxt
        for a, b in segs:
            q = (a, y0, b, y1) if horiz else (x0, a, x1, b)
            cols.append([round(X(q[0]), 3), round(-Y(q[1]), 3), round(X(q[2]), 3), round(-Y(q[3]), 3)])
    for q in getattr(flat, 'EXTRA_COLLIDERS_PX', []):
        cols.append([round(X(q[0]), 3), round(-Y(q[1]), 3), round(X(q[2]), 3), round(-Y(q[3]), 3)])
    furn = []
    for o in bpy.data.objects:
        if o.get('solid') and o.type == 'MESH':
            pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
            xs = [p.x for p in pts]
            ys = [p.y for p in pts]
            furn.append([round(min(xs), 3), round(-max(ys), 3), round(max(xs), 3), round(-min(ys), 3), o.name])
    bx0, by0, bx1, by1 = flat.BOUNDS_PX
    data = dict(id=FLAT, scale=S, ceiling=H, netArea=round(net_area(), 1), rooms=rooms, walls=cols, furniture=furn,
                bounds=[X(bx0), -Y(by0), X(bx1), -Y(by1)], viewRotation=flat.VIEW_ROTATION, **flat.META,
                model=f'assets/{FLAT}/flat.glb', view=f'assets/{FLAT}/view.jpg')
    if hasattr(flat, 'OUTSIDE_PROBE'):          # the room whose light the viewer uses for the outside of the walls
        data['outsideProbe'] = flat.OUTSIDE_PROBE
    out = os.path.join(ROOT, 'data', f'{FLAT}.json')
    old = json.load(open(out)) if os.path.exists(out) else {}
    for k in ('lightmaps', 'lmMax'):          # keep the bake results of the previous run
        if k in old:
            data[k] = old[k]
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w') as f:
        json.dump(data, f, indent=1)


# ---------------------------------------------------------------- main
F.M = M
walls = build_walls()
build_floors()
for key, matname, h in flat.SKIRTING:
    cladding(key, h, matname, thick=0.014 if 'wood' in matname else 0.01, kind='skirting')
for key, h, matname, kw in flat.CLADDING:
    cladding(key, h, matname, kind='tiles', **kw)
for op in OPENINGS:
    sides = side_rooms(op)
    rk = op.get('swing') or (sides[0] if sides[0] in ROOMS else sides[1])
    if op['kind'] in ('door', 'arch'):
        door_frame(op, rk)
    else:
        inside = sides[1] if sides[1] in ROOMS and sides[1] not in flat.OUTDOOR else sides[0]
        window(op, inside)
flat.furnish(types.SimpleNamespace(**globals()))
lighting()
render_settings()
write_scene_json()
os.makedirs(os.path.join(BUILD, FLAT), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BUILD, FLAT, 'flat.blend'))
print('BUILD OK', len(bpy.data.objects), 'objects, net area', round(net_area(), 1))
