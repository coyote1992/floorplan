"""Blender helpers: bmesh primitives, a geometry accumulator, PBR materials and box UVs."""
import bpy
import bmesh
import math
import os
import random
from math import radians, pi, sin, cos
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TEX_SRC = os.path.join(ROOT, 'assets_src', 'tex')
MODELS = os.path.join(ROOT, 'assets_src', 'models')
BUILD = os.path.join(ROOT, 'build')
GEN = os.path.join(BUILD, 'tex')
os.makedirs(GEN, exist_ok=True)

rng = random.Random(42)


# ---------------------------------------------------------------- primitives (bmesh, local coords)
def box(sx, sy, sz, at=(0, 0, 0), bevel=0.0, seg=3, origin='bottom'):
    """Axis aligned box. `at` is the bottom-centre (origin='bottom') or centre."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    ox, oy, oz = at
    dz = sz / 2 if origin == 'bottom' else 0.0
    for v in bm.verts:
        v.co = Vector((v.co.x * sx + ox, v.co.y * sy + oy, v.co.z * sz + oz + dz))
    if bevel > 0:
        b = min(bevel, sx * 0.49, sy * 0.49, sz * 0.49)
        bmesh.ops.bevel(bm, geom=bm.edges[:], offset=b, offset_type='OFFSET', segments=seg,
                        profile=0.5, affect='EDGES', clamp_overlap=True)
    return bm


def box_ext(x0, y0, z0, x1, y1, z1, bevel=0.0, seg=3):
    return box(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0), at=((x0 + x1) / 2, (y0 + y1) / 2, min(z0, z1)),
               bevel=bevel, seg=seg)


def cyl(r, h, at=(0, 0, 0), seg=32, r2=None, bevel=0.0, bseg=2, cap=True, axis='Z'):
    """Cylinder / cone standing on `at` (bottom centre) along Z, or lying along X / Y."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=cap, cap_tris=False, segments=seg, radius1=r,
                          radius2=(r if r2 is None else r2), depth=h)
    for v in bm.verts:
        v.co.z += h / 2
    if bevel > 0 and cap:
        rim = [e for e in bm.edges if len(e.link_faces) == 2 and
               any(len(f.verts) > 4 for f in e.link_faces)]
        if rim:
            bmesh.ops.bevel(bm, geom=rim, offset=min(bevel, r * 0.45), offset_type='OFFSET', segments=bseg,
                            profile=0.5, affect='EDGES', clamp_overlap=True)
    if axis == 'X':
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(pi / 2, 3, 'Y'))
    elif axis == 'Y':
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(-pi / 2, 3, 'X'))
    bmesh.ops.translate(bm, verts=bm.verts, vec=Vector(at))
    return bm


def lathe(profile, seg=48, at=(0, 0, 0), cap_bottom=False, cap_top=False):
    """Surface of revolution. profile = [(r, z), ...]; faces point outward when z grows along the profile."""
    bm = bmesh.new()
    rings = []
    for r, z in profile:
        if r < 1e-6:
            rings.append([bm.verts.new((0, 0, z))])
        else:
            rings.append([bm.verts.new((r * cos(2 * pi * j / seg), r * sin(2 * pi * j / seg), z)) for j in range(seg)])
    for a, b in zip(rings, rings[1:]):
        if len(a) == 1 and len(b) == 1:
            continue
        for j in range(seg):
            k = (j + 1) % seg
            if len(a) == 1:
                bm.faces.new((a[0], b[k], b[j]))
            elif len(b) == 1:
                bm.faces.new((a[j], a[k], b[0]))
            else:
                bm.faces.new((a[j], a[k], b[k], b[j]))
    if cap_bottom and len(rings[0]) > 1:
        bm.faces.new(list(reversed(rings[0])))
    if cap_top and len(rings[-1]) > 1:
        bm.faces.new(rings[-1])
    bmesh.ops.translate(bm, verts=bm.verts, vec=Vector(at))
    return bm


def smooth_path(pts, sub=8):
    """Catmull-Rom through the points."""
    pts = [Vector(p) for p in pts]
    if len(pts) < 3:
        return pts
    out = []
    ext = [pts[0] * 2 - pts[1]] + pts + [pts[-1] * 2 - pts[-2]]
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        for s in range(sub):
            t = s / sub
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(pts[-1])
    return out


def circle2d(r, n=16):
    return [(r * cos(2 * pi * i / n), r * sin(2 * pi * i / n)) for i in range(n)]


def rect2d(w, h, r=0.0, n=3):
    """Rectangle profile w x h centred, optionally with rounded corners."""
    if r <= 0:
        return [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    r = min(r, w / 2 * 0.99, h / 2 * 0.99)
    pts = []
    for cx, cy, a0 in ((w / 2 - r, -h / 2 + r, -90), (w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180)):
        for i in range(n + 1):
            a = radians(a0 + 90 * i / n)
            pts.append((cx + r * cos(a), cy + r * sin(a)))
    return pts


def sweep(path, prof, normal_hint=None, caps=True, closed_path=False):
    """Sweep a closed 2D profile along a 3D polyline (parallel transport frames)."""
    path = [Vector(p) for p in path]
    n = len(path)
    T = []
    for i in range(n):
        a = path[max(i - 1, 0)] if not closed_path else path[(i - 1) % n]
        b = path[min(i + 1, n - 1)] if not closed_path else path[(i + 1) % n]
        T.append((b - a).normalized())
    if normal_hint is not None:
        N = Vector(normal_hint)
    else:
        N = Vector((0, 0, 1)) if abs(T[0].z) < 0.9 else Vector((1, 0, 0))
    N = (N - T[0] * T[0].dot(N)).normalized()
    bm = bmesh.new()
    rings = []
    for i in range(n):
        if i > 0:
            q = T[i - 1].rotation_difference(T[i])
            N = q @ N
            N = (N - T[i] * T[i].dot(N)).normalized()
        B = T[i].cross(N)
        rings.append([bm.verts.new(path[i] + N * px + B * py) for px, py in prof])
    m = len(prof)
    pairs = list(zip(rings, rings[1:])) + ([(rings[-1], rings[0])] if closed_path else [])
    for a, b in pairs:
        for j in range(m):
            k = (j + 1) % m
            bm.faces.new((a[j], a[k], b[k], b[j]))
    if caps and not closed_path:
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def tube(path, r, n=12, sub=6, caps=True):
    return sweep(smooth_path(path, sub) if sub > 1 else path, circle2d(r, n), caps=caps)


def prism(poly, h, at=(0, 0, 0), bevel=0.0, seg=2):
    """Extrude a 2D polygon (CCW) upward by h."""
    bm = bmesh.new()
    bot = [bm.verts.new((x, y, 0)) for x, y in poly]
    top = [bm.verts.new((x, y, h)) for x, y in poly]
    bm.faces.new(list(reversed(bot)))
    bm.faces.new(top)
    m = len(poly)
    for j in range(m):
        k = (j + 1) % m
        bm.faces.new((bot[j], bot[k], top[k], top[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bevel, offset_type='OFFSET', segments=seg,
                        profile=0.5, affect='EDGES', clamp_overlap=True)
    bmesh.ops.translate(bm, verts=bm.verts, vec=Vector(at))
    return bm


def grid_surface(fn, nu, nv):
    """Parametric surface; fn(u, v) -> (x, y, z) with u, v in [0, 1]. Single sided."""
    bm = bmesh.new()
    vs = [[bm.verts.new(fn(i / nu, j / nv)) for j in range(nv + 1)] for i in range(nu + 1)]
    for i in range(nu):
        for j in range(nv):
            bm.faces.new((vs[i][j], vs[i + 1][j], vs[i + 1][j + 1], vs[i][j + 1]))
    return bm


def xform(bm, loc=(0, 0, 0), rz=0.0, rx=0.0, ry=0.0, scale=None):
    M = Matrix.Translation(Vector(loc)) @ Matrix.Rotation(rz, 4, 'Z') @ Matrix.Rotation(ry, 4, 'Y') @ Matrix.Rotation(rx, 4, 'X')
    if scale is not None:
        s = scale if isinstance(scale, (tuple, list)) else (scale, scale, scale)
        M = M @ Matrix.Diagonal((s[0], s[1], s[2], 1))
    bm.transform(M)
    return bm


def boolean(bm_a, bm_b, op='DIFFERENCE'):
    """Exact boolean of two bmeshes (consumed). Returns a new bmesh."""
    sc = bpy.context.scene.collection
    objs = []
    for nm, b in (('_bool_a', bm_a), ('_bool_b', bm_b)):
        me = bpy.data.meshes.new(nm)
        b.to_mesh(me)
        b.free()
        o = bpy.data.objects.new(nm, me)
        sc.objects.link(o)
        objs.append(o)
    oa, ob = objs
    mod = oa.modifiers.new('bool', 'BOOLEAN')
    mod.operation = op
    mod.object = ob
    mod.solver = 'EXACT'
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    out = bmesh.new()
    out.from_object(oa, dg)
    for o in objs:
        me = o.data
        bpy.data.objects.remove(o)
        bpy.data.meshes.remove(me)
    return out


def open_box(sx, sy, sz, at=(0, 0, 0), inward=True):
    """Box without its top face; normals inward (for basins / drawers seen from inside)."""
    bm = box(sx, sy, sz, at=at)
    top = [f for f in bm.faces if f.normal.z > 0.9]
    bmesh.ops.delete(bm, geom=top, context='FACES_ONLY')
    if inward:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    return bm


def fit_uv(ob, plane='xy', flip_u=False):
    """Map UVs 0..1 across the object's local bounding box (rugs, posters, curtains)."""
    me = ob.data
    uvl = me.uv_layers['UVMap']
    a = {'x': 0, 'y': 1, 'z': 2}
    ia, ib = a[plane[0]], a[plane[1]]
    xs = [v.co[ia] for v in me.vertices]
    ys = [v.co[ib] for v in me.vertices]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    for li, lp in enumerate(me.loops):
        co = me.vertices[lp.vertex_index].co
        u = (co[ia] - x0) / max(1e-6, x1 - x0)
        uvl.data[li].uv = ((1 - u) if flip_u else u, (co[ib] - y0) / max(1e-6, y1 - y0))


# ---------------------------------------------------------------- geometry accumulator
class Geo:
    """Collects bmesh pieces with materials into one mesh object."""

    def __init__(self):
        self.v, self.f, self.fm, self.fg, self.fo = [], [], [], [], []
        self.mats = []

    def add(self, bm, mat, grain=None, jitter=True, **tf):
        if tf:
            xform(bm, **tf)
        if jitter and len(bm.verts) > 0:
            # grow each piece by a random 0.2-1.2 mm so that no two pieces share a coplanar face
            # (coincident faces shade black in Cycles and in the baked lightmaps)
            xs = [v.co.x for v in bm.verts]
            ys = [v.co.y for v in bm.verts]
            zs = [v.co.z for v in bm.verts]
            c = Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2))
            half = Vector(((max(xs) - min(xs)) / 2, (max(ys) - min(ys)) / 2, (max(zs) - min(zs)) / 2))
            hsh = hash((round(c.x, 4), round(c.y, 4), round(c.z, 4), round(half.x, 4), round(half.y, 4), round(half.z, 4)))
            e = 0.0002 + (hsh % 997) / 997 * 0.001        # deterministic per piece (stable lightmap UVs between builds)
            k = Vector(tuple(1 + e / h if h > 1e-5 else 1.0 for h in half))
            for v in bm.verts:
                d = v.co - c
                v.co = c + Vector((d.x * k.x, d.y * k.y, d.z * k.z))
        if mat not in self.mats:
            self.mats.append(mat)
        mi = self.mats.index(mat)
        bm.verts.index_update()
        off = len(self.v)
        self.v.extend(v.co.copy() for v in bm.verts)
        hv = hash(tuple(round(v.co[i], 3) for v in bm.verts[:3] for i in range(3))) if len(bm.verts) else 0
        o = ((hv % 7919) / 7919 * 7, (hv // 7919 % 7907) / 7907 * 7)
        for fc in bm.faces:
            self.f.append([off + v.index for v in fc.verts])
            self.fm.append(mi)
            self.fg.append(grain)
            self.fo.append(o)
        bm.free()
        return self

    def merge(self, other, **tf):
        M = Matrix.Translation(Vector(tf.get('loc', (0, 0, 0)))) @ Matrix.Rotation(tf.get('rz', 0.0), 4, 'Z')
        off = len(self.v)
        self.v.extend(M @ v for v in other.v)
        for f, mi, g, o in zip(other.f, other.fm, other.fg, other.fo):
            mat = other.mats[mi]
            if mat not in self.mats:
                self.mats.append(mat)
            self.f.append([off + i for i in f])
            self.fm.append(self.mats.index(mat))
            self.fg.append(g)
            self.fo.append(o)
        return self


COLLS = {}


def coll(name):
    if name not in COLLS:
        c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
        if c.name not in bpy.context.scene.collection.children:
            bpy.context.scene.collection.children.link(c)
        COLLS[name] = c
    return COLLS[name]


def make(name, geo, loc=(0, 0, 0), rz=0.0, collection='furniture', room=None, smooth=38, props=None,
         lightmap=True, solid=False):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in geo.v], [], geo.f)
    me.validate(clean_customdata=False)
    for m in geo.mats:
        me.materials.append(m)
    if len(me.polygons) == len(geo.fm):
        me.polygons.foreach_set('material_index', geo.fm)
    if smooth is not None:
        me.shade_smooth()
        me.set_sharp_from_angle(angle=radians(smooth))
    else:
        me.shade_flat()
    box_uv(me, geo.fg if len(me.polygons) == len(geo.fg) else None, geo.fo if len(me.polygons) == len(geo.fo) else None)
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    ob.rotation_euler = (0, 0, rz)
    coll(collection).objects.link(ob)
    if room:
        ob['room'] = room
    ob['lightmap'] = bool(lightmap)
    if solid:
        ob['solid'] = 1
    for k, v in (props or {}).items():
        ob[k] = v
    return ob


def box_uv(me, grains=None, offsets=None):
    """World-scale box projection per face; tile size comes from each material's 'tile' property."""
    uvl = me.uv_layers.get('UVMap') or me.uv_layers.new(name='UVMap')
    verts = me.vertices
    loops = me.loops
    tiles = [float(m.get('tile', 1.0)) if m else 1.0 for m in me.materials] or [1.0]
    for p in me.polygons:
        n = p.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        plane = [i for i in range(3) if i != ax]
        g = grains[p.index] if grains else None
        if g is not None and g in plane:
            u_ax = [i for i in plane if i != g][0]
            v_ax = g
        else:
            u_ax, v_ax = plane
            if ax == 2:
                u_ax, v_ax = 0, 1
        t = tiles[p.material_index] if p.material_index < len(tiles) else 1.0
        o = offsets[p.index] if offsets else (0, 0)
        for li in p.loop_indices:
            co = verts[loops[li].vertex_index].co
            uvl.data[li].uv = (co[u_ax] / t + o[0], co[v_ax] / t + o[1])


# ---------------------------------------------------------------- materials
MATS = {}


def load_img(path, noncolor=False):
    im = bpy.data.images.load(path, check_existing=True)
    if noncolor:
        im.colorspace_settings.name = 'Non-Color'
    return im


def acg(asset, res=None):
    """Paths of an ambientCG asset folder."""
    d = os.path.join(TEX_SRC, asset)
    files = os.listdir(d)

    def f(kind):
        for fn in files:
            if fn.endswith('_' + kind + '.jpg'):
                return os.path.join(d, fn)
        return None
    return dict(color=f('Color'), rough=f('Roughness'), normal=f('NormalGL'))


def mat(name, color=(0.8, 0.8, 0.8), rough=0.5, metal=0.0, tex=None, tile=1.0, normal=1.0, alpha=1.0,
        emission=None, strength=0.0, double=False, transmission=0.0, coat=0.0, spec=0.5):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    b = N['Principled BSDF']
    c = tuple(color) + (1.0,) if len(color) == 3 else tuple(color)
    b.inputs['Base Color'].default_value = c
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    b.inputs['Specular IOR Level'].default_value = spec
    if coat > 0:
        b.inputs['Coat Weight'].default_value = coat
        b.inputs['Coat Roughness'].default_value = 0.08
    if tex:
        uv = N.new('ShaderNodeUVMap')
        uv.uv_map = 'UVMap'
        uv.location = (-900, 0)
        if tex.get('color'):
            t = N.new('ShaderNodeTexImage')
            t.image = load_img(tex['color'])
            t.location = (-600, 300)
            L.new(uv.outputs['UV'], t.inputs['Vector'])
            L.new(t.outputs['Color'], b.inputs['Base Color'])
        if tex.get('rough'):
            t = N.new('ShaderNodeTexImage')
            t.image = load_img(tex['rough'], True)
            t.location = (-600, 0)
            L.new(uv.outputs['UV'], t.inputs['Vector'])
            L.new(t.outputs['Color'], b.inputs['Roughness'])
        if tex.get('normal') and normal > 0:
            t = N.new('ShaderNodeTexImage')
            t.image = load_img(tex['normal'], True)
            t.location = (-600, -300)
            nm = N.new('ShaderNodeNormalMap')
            nm.inputs['Strength'].default_value = normal
            nm.location = (-300, -300)
            L.new(uv.outputs['UV'], t.inputs['Vector'])
            L.new(t.outputs['Color'], nm.inputs['Color'])
            L.new(nm.outputs['Normal'], b.inputs['Normal'])
    if alpha < 1.0:
        b.inputs['Alpha'].default_value = alpha
        m.blend_method = 'BLEND'
        m['alpha'] = alpha
    if transmission > 0:
        b.inputs['Transmission Weight'].default_value = transmission
    if emission is not None:
        b.inputs['Emission Color'].default_value = tuple(emission) + (1.0,)
        b.inputs['Emission Strength'].default_value = strength
        m['emissive'] = strength
    m.use_backface_culling = not double
    m['tile'] = tile
    MATS[name] = m
    return m
