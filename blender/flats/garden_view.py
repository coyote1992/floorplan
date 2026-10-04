"""Garden flat: render the view out of the windows as an equirectangular panorama.
   blender -b -P blender/flats/garden_view.py        -> assets/garden/view.jpg
The flat is on a raised ground floor; the windows look south over a lawn with a gazebo,
a planted bed, an ivy-covered tree, a hedge and neighbouring houses (from the garden photos)."""
import os
import sys
import random
from math import radians, pi, sin, cos
import bpy
import bmesh
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.environ.get('PANO_OUT', os.path.join(ROOT, 'assets', 'garden', 'view.jpg'))
RES = int(os.environ.get('PANO_RES', '4096'))
SAMPLES = int(os.environ.get('PANO_SAMPLES', '48'))
G = -0.75                      # lawn level relative to the flat's floor
CX, CY = 4.6, -3.9             # camera: living room centre (Blender metres)
FACADE = -6.66                 # outer face of the south wall
rnd = random.Random(11)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene


def mat(name, color, rough=0.8, noise=None, alpha=1.0, scale=6.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = color + (1,)
    b.inputs['Roughness'].default_value = rough
    if noise:
        oi = nt.nodes.new('ShaderNodeObjectInfo')
        ramp = nt.nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].color = noise[0] + (1,)
        ramp.color_ramp.elements[1].color = noise[1] + (1,)
        if len(noise) > 2:
            e = ramp.color_ramp.elements.new(0.5)
            e.color = noise[2] + (1,)
        nt.links.new(oi.outputs['Random'], ramp.inputs['Fac'])
        tex = nt.nodes.new('ShaderNodeTexNoise')
        tex.inputs['Scale'].default_value = scale
        mix = nt.nodes.new('ShaderNodeMix')
        mix.data_type = 'RGBA'
        mix.blend_type = 'MULTIPLY'
        mix.inputs['Factor'].default_value = 0.35
        nt.links.new(ramp.outputs['Color'], mix.inputs['A'])
        nt.links.new(tex.outputs['Color'], mix.inputs['B'])
        nt.links.new(mix.outputs['Result'], b.inputs['Base Color'])
    if alpha < 1:
        b.inputs['Alpha'].default_value = alpha
    return m


def obj(name, bm, m, smooth=False):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    sc.collection.objects.link(o)
    me.materials.append(m)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    return o


def plane(name, x0, y0, x1, y1, z, m):
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in ((x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z))]
    bm.faces.new(vs)
    return obj(name, bm, m)


def cube(name, x0, y0, z0, x1, y1, z1, m):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector(((v.co.x + 0.5) * (x1 - x0) + x0, (v.co.y + 0.5) * (y1 - y0) + y0, (v.co.z + 0.5) * (z1 - z0) + z0))
    return obj(name, bm, m)


# ---------------------------------------------------------------- ground
lawn = mat('lawn', (0.16, 0.30, 0.07), 0.95, noise=((0.14, 0.28, 0.06), (0.24, 0.36, 0.09)), scale=220.0)
paving = mat('paving', (0.45, 0.43, 0.40), 0.85)
soil = mat('soil', (0.14, 0.10, 0.07), 0.95)
wood = mat('fence', (0.45, 0.33, 0.22), 0.8)
plane('lawn', -80, 3, 80, -120, G, lawn)
plane('far', -800, 900, 800, -900, G - 0.4, mat('fields', (0.24, 0.33, 0.12), 0.95))
cube('terrace', -20, FACADE - 1.2, G, 20, FACADE, G + 0.04, paving)
for i in range(7):                                        # stepping stones from the garden door
    x = 5.9 - i * 0.7 + rnd.uniform(-0.1, 0.1)
    y = FACADE - 1.6 - i * 0.72
    cube(f'stone{i}', x - 0.22, y - 0.18, G, x + 0.22, y + 0.18, G + 0.025, paving)

# planted bed with a low log edging
bx0, by0, bx1, by1 = 3.2, -12.0, 7.4, -15.2
cube('bed', bx0, by1, G, bx1, by0, G + 0.05, soil)
for (x0, y0, x1, y1) in ((bx0, by0, bx1, by0 + 0.08), (bx0, by1 - 0.08, bx1, by1), (bx0 - 0.08, by1, bx0, by0), (bx1, by1, bx1 + 0.08, by0)):
    cube('edge', x0, y0, G, x1, y1, G + 0.16, wood)

# ---------------------------------------------------------------- vegetation (instanced blobs)
leaf = mat('leaves', (0.20, 0.33, 0.10), 0.85, noise=((0.12, 0.26, 0.07), (0.32, 0.42, 0.12), (0.22, 0.36, 0.09)))
autumn = mat('autumn', (0.45, 0.32, 0.12), 0.85, noise=((0.42, 0.30, 0.10), (0.30, 0.34, 0.11), (0.55, 0.38, 0.14)))
bark = mat('bark', (0.20, 0.15, 0.11), 0.9)

blob_mesh = bpy.data.meshes.new('blob')
bm = bmesh.new()
for (ox, oy, oz, r) in ((0, 0, 0.0, 1.0), (0.5, 0.2, -0.25, 0.7), (-0.45, -0.25, -0.2, 0.72), (0.1, -0.45, 0.35, 0.6),
                        (-0.15, 0.4, 0.4, 0.55)):
    tmp = bmesh.new()
    bmesh.ops.create_icosphere(tmp, subdivisions=3, radius=r)
    for v in tmp.verts:
        v.co *= 1 + 0.10 * sin(v.co.x * 11 + ox) * cos(v.co.y * 9 + oy) + 0.06 * sin(v.co.z * 15)
        v.co += Vector((ox, oy, oz))
    me_t = bpy.data.meshes.new('_t')
    tmp.to_mesh(me_t)
    tmp.free()
    bm.from_mesh(me_t)
    bpy.data.meshes.remove(me_t)
bm.to_mesh(blob_mesh)
bm.free()
for p in blob_mesh.polygons:
    p.use_smooth = True
blob_mesh.materials.append(leaf)


def blob(x, y, z, sx, sy, sz, m, rot=None):
    o = bpy.data.objects.new('b', blob_mesh)
    o.location = (x, y, z)
    o.scale = (sx, sy, sz)
    o.rotation_euler = (0, 0, rot if rot is not None else rnd.uniform(0, 6.28))
    sc.collection.objects.link(o)
    o.material_slots[0].link = 'OBJECT'
    o.material_slots[0].material = m
    return o


def trunk(x, y, h, r):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=r, radius2=r * 0.6, depth=h)
    for v in bm.verts:
        v.co += Vector((x, y, G + h / 2))
    obj('trunk', bm, bark, smooth=True)


def tree(x, y, h, w, m=leaf):
    trunk(x, y, h * 0.55, w * 0.06 + 0.08)
    for k in range(4):
        blob(x + rnd.uniform(-0.3, 0.3) * w, y + rnd.uniform(-0.3, 0.3) * w, G + h * (0.55 + 0.12 * k),
             w * rnd.uniform(0.45, 0.6), w * rnd.uniform(0.45, 0.6), h * rnd.uniform(0.16, 0.22), m)


# big deciduous trees and the ivy-covered column
tree(9.5, -34, 13, 7, autumn)
tree(-9, -36, 11, 6)
tree(-15, -26, 9, 5)
tree(18, -25, 8, 5)
for k in range(10):                                      # trees in the neighbouring gardens, east and west
    tree(-18 - rnd.uniform(0, 30), rnd.uniform(-2, -36), rnd.uniform(7, 11), rnd.uniform(4, 6), rnd.choice((leaf, leaf, autumn)))
    tree(22 + rnd.uniform(0, 30), rnd.uniform(-2, -36), rnd.uniform(7, 11), rnd.uniform(4, 6), rnd.choice((leaf, leaf, autumn)))
for k in range(9):                                       # ivy column
    blob(3.2 + rnd.uniform(-0.4, 0.4), -21 + rnd.uniform(-0.4, 0.4), G + 0.8 + k * 0.85, 1.25 - k * 0.05, 1.2 - k * 0.05, 0.75, leaf)
# shrubs in the bed and around the lawn
for k in range(8):
    blob(rnd.uniform(bx0 + 0.4, bx1 - 0.4), rnd.uniform(by1 + 0.4, by0 - 0.4), G + 0.5, 0.5, 0.5, 0.6, leaf)
blob(5.6, -13.4, G + 1.4, 0.9, 0.8, 1.5, leaf)           # young tree in the bed
for k in range(28):                                      # hedge at the back of the garden
    x = -22 + k * 1.7
    blob(x, -31 + rnd.uniform(-0.4, 0.4), G + 1.1, 1.2, 0.9, 1.3, leaf)
for k in range(10):                                      # shrubs along the sides
    blob(-12 + rnd.uniform(-1, 1), -9 - k * 2.0, G + 0.8, 1.0, 1.0, 1.0, leaf)
    blob(15 + rnd.uniform(-1, 1), -8 - k * 2.0, G + 0.9, 1.1, 1.0, 1.1, leaf)
for k in range(5):                                       # ornamental grass by the gazebo
    blob(-3.0 + rnd.uniform(-0.3, 0.3), -11.0 + rnd.uniform(-0.3, 0.3), G + 0.5, 0.25, 0.25, 0.7,
         mat(f'grass{k}', (0.42, 0.45, 0.22), 0.9))

# ---------------------------------------------------------------- gazebo with curtains and fence panels
gx, gy, gr = -3.6, -12.5, 1.8
metal = mat('gazebo_frame', (0.25, 0.25, 0.27), 0.5)
canopy = mat('canopy', (0.22, 0.22, 0.26), 0.8)
drape = mat('drape', (0.40, 0.40, 0.45), 0.9)
for k in range(8):
    a = k * pi / 4
    x, y = gx + gr * cos(a), gy + gr * sin(a)
    cube('post', x - 0.03, y - 0.03, G, x + 0.03, y + 0.03, G + 2.35, metal)
    if k % 2 == 0:
        cube('drape', x - 0.12, y - 0.12, G + 0.1, x + 0.12, y + 0.12, G + 2.3, drape)
bm = bmesh.new()
bmesh.ops.create_cone(bm, cap_ends=False, segments=16, radius1=gr + 0.35, radius2=0.15, depth=1.0)
for v in bm.verts:
    v.co += Vector((gx, gy, G + 2.85))
obj('canopy', bm, canopy, smooth=True)
cube('table', gx - 0.6, gy - 0.4, G + 0.7, gx + 0.6, gy + 0.4, G + 0.75, wood)
for k in range(5):                                       # wooden privacy screen behind the gazebo
    x0 = gx - 2.6 + k * 1.0
    cube('fence', x0, gy - 2.4, G, x0 + 0.95, gy - 2.35, G + 1.8, wood)

# ---------------------------------------------------------------- neighbouring houses beyond the hedge
wall_m = mat('houses', (0.86, 0.82, 0.74), 0.85, noise=((0.90, 0.86, 0.78), (0.80, 0.74, 0.64)))
roof_m = mat('roofs', (0.45, 0.20, 0.13), 0.7, noise=((0.48, 0.22, 0.14), (0.32, 0.28, 0.27)))
for k in range(16):
    x = -60 + k * 8 + rnd.uniform(-2, 2)
    y = -42 - rnd.uniform(0, 30)
    w, d, h = rnd.uniform(7, 11), rnd.uniform(7, 10), rnd.uniform(5, 8)
    cube('house', x - w / 2, y - d / 2, G, x + w / 2, y + d / 2, G + h, wall_m)
    bm = bmesh.new()
    a = [bm.verts.new(p) for p in ((x - w / 2 - 0.4, y - d / 2 - 0.4, G + h), (x + w / 2 + 0.4, y - d / 2 - 0.4, G + h),
                                   (x + w / 2 + 0.4, y + d / 2 + 0.4, G + h), (x - w / 2 - 0.4, y + d / 2 + 0.4, G + h))]
    t1 = bm.verts.new((x - w / 2 - 0.4, y, G + h + d * 0.45))
    t2 = bm.verts.new((x + w / 2 + 0.4, y, G + h + d * 0.45))
    bm.faces.new((a[0], a[1], t2, t1))
    bm.faces.new((a[2], a[3], t1, t2))
    bm.faces.new((a[1], a[2], t2))
    bm.faces.new((a[3], a[0], t1))
    obj('roof', bm, roof_m)
for k in range(140):                                      # trees between the houses
    tree(rnd.uniform(-90, 90), rnd.uniform(-38, -110), rnd.uniform(7, 13), rnd.uniform(4, 7), rnd.choice((leaf, leaf, autumn)))

# flower pots and low shrubs along the terrace edge
pot_m = mat('pots', (0.42, 0.20, 0.12), 0.8)
for x in (-0.6, 2.4, 8.2, 10.6):
    cube('pot', x - 0.2, FACADE - 1.0, G + 0.04, x + 0.2, FACADE - 0.6, G + 0.42, pot_m)
    blob(x, FACADE - 0.8, G + 0.62, 0.32, 0.32, 0.36, leaf)
for k in range(12):
    x = -6 + k * 1.9 + rnd.uniform(-0.3, 0.3)
    if abs(x - 5.9) > 1.1:                                # keep the path to the door clear
        blob(x, FACADE - 1.55 + rnd.uniform(-0.1, 0.1), G + 0.25, 0.45, 0.35, 0.35, leaf)

# ---------------------------------------------------------------- sky, sun, camera
world = bpy.data.worlds.new('World')
sc.world = world
world.use_nodes = True
nt = world.node_tree
sky = nt.nodes.new('ShaderNodeTexSky')
sky.sky_type = 'NISHITA'
sky.sun_disc = False
sky.sun_elevation = radians(30)
sky.sun_rotation = radians(180 + 22)
sky.altitude = 300
sky.air_density = 1.2
sky.dust_density = 1.4
nt.links.new(sky.outputs['Color'], nt.nodes['Background'].inputs['Color'])
nt.nodes['Background'].inputs['Strength'].default_value = 1.0
sun = bpy.data.lights.new('Sun', 'SUN')
sun.energy = 45.0
sun.angle = radians(0.8)
sun.color = (1.0, 0.88, 0.74)
so = bpy.data.objects.new('Sun', sun)
sc.collection.objects.link(so)
el, az = radians(30), radians(158)
d = Vector((sin(az) * cos(el), cos(az) * cos(el), sin(el)))
so.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()

cam = bpy.data.cameras.new('pano')
cam.type = 'PANO'
cam.panorama_type = 'EQUIRECTANGULAR'
cam.clip_start = 0.05
cam.clip_end = 5000
co = bpy.data.objects.new('pano', cam)
co.location = (CX, CY, 1.6)
co.rotation_euler = (pi / 2, 0, pi)       # image centre looks south (-Y), into the garden
sc.collection.objects.link(co)
sc.camera = co

sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True
sc.render.resolution_x = RES
sc.render.resolution_y = RES // 2
sc.view_settings.view_transform = 'AgX'
sc.view_settings.look = 'AgX - Medium High Contrast'
sc.view_settings.exposure = float(os.environ.get('PANO_EXP', '-2.6'))
sc.render.image_settings.file_format = 'JPEG'
sc.render.image_settings.quality = 88
os.makedirs(os.path.dirname(OUT), exist_ok=True)
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print('PANORAMA OK', OUT)
