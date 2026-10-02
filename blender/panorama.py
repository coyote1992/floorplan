"""Render the view out of the windows as an equirectangular panorama (web/assets/view.jpg).
The flat is on a high floor of a panel block: a park below the windows, the river, the far bank
with trees and houses, and wooded hills behind, like in the photos.  blender -b -P blender/panorama.py"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import bmesh
import random
from math import radians, pi, sin, cos
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.environ.get('PANO_OUT', os.path.join(ROOT, 'assets', 'view.jpg'))
RES = int(os.environ.get('PANO_RES', '6144'))
SAMPLES = int(os.environ.get('PANO_SAMPLES', '64'))
FLOOR_HEIGHT = 30.0          # height of the flat's floor above the park
CX, CY = 3.6, -5.2           # flat centre in Blender metres (plan origin is the NW corner)
rnd = random.Random(3)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
G = -FLOOR_HEIGHT


def mat(name, color, rough=0.8, metal=0.0, noise=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = color + (1,)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if noise:
        # random per-instance colour between two tones (trees, houses)
        oi = nt.nodes.new('ShaderNodeObjectInfo')
        ramp = nt.nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].color = noise[0] + (1,)
        ramp.color_ramp.elements[1].color = noise[1] + (1,)
        if len(noise) > 2:
            e = ramp.color_ramp.elements.new(0.5)
            e.color = noise[2] + (1,)
        nt.links.new(oi.outputs['Random'], ramp.inputs['Fac'])
        tex = nt.nodes.new('ShaderNodeTexNoise')
        tex.inputs['Scale'].default_value = 8.0
        mix = nt.nodes.new('ShaderNodeMix')
        mix.data_type = 'RGBA'
        mix.blend_type = 'MULTIPLY'
        mix.inputs['Factor'].default_value = 0.35
        nt.links.new(ramp.outputs['Color'], mix.inputs['A'])
        nt.links.new(tex.outputs['Color'], mix.inputs['B'])
        nt.links.new(mix.outputs['Result'], b.inputs['Base Color'])
    return m


def obj(name, bm, m):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    sc.collection.objects.link(o)
    me.materials.append(m)
    return o


def plane(name, x0, y0, x1, y1, z, m):
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in ((x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z))]
    bm.faces.new(vs)
    return obj(name, bm, m)


# ---------------------------------------------------------------- terrain
grass = mat('grass', (0.20, 0.27, 0.10), 0.95)
park = mat('park', (0.24, 0.30, 0.12), 0.95)
water = mat('water', (0.10, 0.16, 0.18), 0.06)
bank = mat('bank', (0.55, 0.50, 0.40), 0.9)
road = mat('road', (0.30, 0.30, 0.31), 0.8)
plane('ground', -6000, -6000, 6000, 6000, G - 8.0, grass)
# windows face +Y (plan north). Park below, embankment road, river, far bank.
plane('park', -3000, -3000, 3000, 120, G, park)
plane('road', -900, 120, 900, 138, G + 0.05, road)
plane('bank_near', -900, 138, 900, 150, G - 1.5, bank)
plane('river', -3000, 150, 3000, 520, G - 3.0, water)
plane('bank_far', -3000, 520, 3000, 540, G - 1.5, bank)
plane('far_land', -6000, 540, 6000, 6000, G + 0.5, grass)

# hills: displaced grid
hill_m = mat('hills', (0.30, 0.34, 0.16), 0.95, noise=((0.28, 0.33, 0.14), (0.45, 0.38, 0.17)))
bm = bmesh.new()
nx, ny = 160, 60
verts = []
for j in range(ny + 1):
    row = []
    for i in range(nx + 1):
        x = -5000 + 10000 * i / nx
        y = 1100 + 3200 * j / ny
        t = j / ny
        h = (sin(x / 900.0) * 0.5 + 0.5) * 120 + (sin(x / 370.0 + 1.3) * 0.5 + 0.5) * 60
        h += 330 * (1 - (1 - t) ** 2) + 90 * sin(x / 1500 + 0.4)
        h *= min(1.0, t * 4 + 0.15)
        row.append(bm.verts.new((x, y, G + h)))
    verts.append(row)
for j in range(ny):
    for i in range(nx):
        bm.faces.new((verts[j][i], verts[j][i + 1], verts[j + 1][i + 1], verts[j + 1][i]))
hills = obj('hills', bm, hill_m)
for p in hills.data.polygons:
    p.use_smooth = True


def hill_z(x, y):
    t = (y - 1100) / 3200
    if t < 0:
        return G
    h = (sin(x / 900.0) * 0.5 + 0.5) * 120 + (sin(x / 370.0 + 1.3) * 0.5 + 0.5) * 60
    h += 330 * (1 - (1 - t) ** 2) + 90 * sin(x / 1500 + 0.4)
    h *= min(1.0, t * 4 + 0.15)
    return G + h


# ---------------------------------------------------------------- trees and houses (instanced)
tree_m = mat('trees', (0.25, 0.33, 0.12), 0.9, noise=((0.17, 0.27, 0.09), (0.62, 0.42, 0.12), (0.33, 0.40, 0.13)))
house_m = mat('houses', (0.85, 0.80, 0.70), 0.8, noise=((0.92, 0.88, 0.80), (0.80, 0.70, 0.58)))
roof_m = mat('roofs', (0.45, 0.20, 0.13), 0.7, noise=((0.50, 0.22, 0.14), (0.30, 0.28, 0.27)))
block_m = mat('blocks', (0.78, 0.76, 0.72), 0.85)
_nt = block_m.node_tree
_geo = _nt.nodes.new('ShaderNodeNewGeometry')
_brick = _nt.nodes.new('ShaderNodeTexBrick')
_brick.offset = 0.0
_brick.squash = 1.0
_brick.inputs['Scale'].default_value = 1.0
_brick.inputs['Mortar Size'].default_value = 0.55
_brick.inputs['Brick Width'].default_value = 2.4
_brick.inputs['Row Height'].default_value = 2.8
_brick.inputs['Color1'].default_value = (0.20, 0.24, 0.28, 1)
_brick.inputs['Color2'].default_value = (0.28, 0.31, 0.34, 1)
_brick.inputs['Mortar'].default_value = (0.80, 0.78, 0.73, 1)
_sep = _nt.nodes.new('ShaderNodeSeparateXYZ')
_comb = _nt.nodes.new('ShaderNodeCombineXYZ')
_nt.links.new(_geo.outputs['Position'], _sep.inputs['Vector'])
_add = _nt.nodes.new('ShaderNodeMath')
_add.operation = 'ADD'
_nt.links.new(_sep.outputs['X'], _add.inputs[0])
_nt.links.new(_sep.outputs['Y'], _add.inputs[1])
_nt.links.new(_add.outputs['Value'], _comb.inputs['X'])
_nt.links.new(_sep.outputs['Z'], _comb.inputs['Y'])
_nt.links.new(_comb.outputs['Vector'], _brick.inputs['Vector'])
_nt.links.new(_brick.outputs['Color'], _nt.nodes['Principled BSDF'].inputs['Base Color'])

tree_mesh = bpy.data.meshes.new('tree')
bm = bmesh.new()
# a canopy made of a few lumpy blobs on a short trunk
for (ox, oy, oz, r) in ((0, 0, 1.25, 1.0), (0.45, 0.2, 0.95, 0.7), (-0.4, -0.25, 1.0, 0.72), (0.1, -0.45, 1.55, 0.6), (-0.15, 0.4, 1.6, 0.55)):
    tmp = bmesh.new()
    bmesh.ops.create_icosphere(tmp, subdivisions=2, radius=r)
    for v in tmp.verts:
        v.co *= 1 + 0.12 * sin(v.co.x * 9 + ox) * cos(v.co.y * 7 + oy) + 0.06 * sin(v.co.z * 13)
        v.co += Vector((ox, oy, oz))
    me_t = bpy.data.meshes.new('_t')
    tmp.to_mesh(me_t)
    tmp.free()
    bm.from_mesh(me_t)
    bpy.data.meshes.remove(me_t)
bm.to_mesh(tree_mesh)
bm.free()
tree_mesh.materials.append(tree_m)
for p in tree_mesh.polygons:
    p.use_smooth = True


def tree(x, y, z, s):
    o = bpy.data.objects.new('t', tree_mesh)
    o.location = (x, y, z)
    o.scale = (s * rnd.uniform(0.8, 1.2), s * rnd.uniform(0.8, 1.2), s * rnd.uniform(0.9, 1.4))
    o.rotation_euler = (0, 0, rnd.uniform(0, 6.28))
    sc.collection.objects.link(o)


house_mesh = bpy.data.meshes.new('house')
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=1.0)
for v in bm.verts:
    v.co.z += 0.5
bm.to_mesh(house_mesh)
bm.free()
house_mesh.materials.append(house_m)
block_mesh = house_mesh.copy()
block_mesh.materials[0] = block_m
roof_mesh = bpy.data.meshes.new('roof')
bm = bmesh.new()
a = [bm.verts.new(p) for p in ((-0.55, -0.55, 0), (0.55, -0.55, 0), (0.55, 0.55, 0), (-0.55, 0.55, 0))]
t1 = bm.verts.new((0, -0.2, 0.45))
t2 = bm.verts.new((0, 0.2, 0.45))
bm.faces.new((a[0], a[1], t1))
bm.faces.new((a[1], a[2], t2, t1))
bm.faces.new((a[2], a[3], t2))
bm.faces.new((a[3], a[0], t1, t2))
bm.to_mesh(roof_mesh)
bm.free()
roof_mesh.materials.append(roof_m)


def house(x, y, z, w, d, h, rot):
    o = bpy.data.objects.new('h', house_mesh)
    o.location = (x, y, z)
    o.scale = (w, d, h)
    o.rotation_euler = (0, 0, rot)
    sc.collection.objects.link(o)
    r = bpy.data.objects.new('r', roof_mesh)
    r.location = (x, y, z + h)
    r.scale = (w, d, h * 0.6)
    r.rotation_euler = (0, 0, rot)
    sc.collection.objects.link(r)


# park trees below the windows (some close, tall)
for i in range(2600):
    x, y = rnd.uniform(-700, 700), rnd.uniform(10, 118)
    tree(x, y, G, rnd.uniform(2.8, 4.6))
for i in range(900):   # strip of trees along the embankment road
    x, y = rnd.uniform(-1500, 1500), rnd.uniform(140, 148)
    tree(x, y, G - 1.5, rnd.uniform(3.0, 4.5))
# trees along the far bank
for i in range(700):
    x, y = rnd.uniform(-2500, 2500), rnd.uniform(545, 700)
    tree(x, y, G + 0.5, rnd.uniform(3.5, 6))
# far-bank town: houses and blocks
for i in range(500):
    x, y = rnd.uniform(-2500, 2500), rnd.uniform(700, 1150)
    if rnd.random() < 0.15:
        o = bpy.data.objects.new('b', house_mesh)
        o.location = (x, y, G + 0.5)
        o.scale = (rnd.uniform(14, 40), rnd.uniform(12, 16), rnd.uniform(12, 30))
        o.rotation_euler = (0, 0, rnd.choice((0, 1.57)) + rnd.uniform(-0.1, 0.1))
        o.data = house_mesh
        sc.collection.objects.link(o)
    else:
        house(x, y, G + 0.5, rnd.uniform(9, 16), rnd.uniform(8, 13), rnd.uniform(6, 10), rnd.uniform(0, 3.14))
    if rnd.random() < 0.8:
        tree(x + rnd.uniform(-20, 20), y + rnd.uniform(-20, 20), G + 0.5, rnd.uniform(3, 5))
# villas and forest on the hills
for i in range(2600):
    x, y = rnd.uniform(-4500, 4500), rnd.uniform(1150, 4200)
    z = hill_z(x, y)
    if rnd.random() < 0.2 and y < 2600:
        house(x, y, z - 1, rnd.uniform(10, 18), rnd.uniform(9, 14), rnd.uniform(6, 9), rnd.uniform(0, 3.14))
    else:
        tree(x, y, z - 2, rnd.uniform(9, 16))
# panel blocks behind the flat (kitchen side) and to the sides
for i in range(16):
    ang = rnd.uniform(pi * 1.15, pi * 1.85)
    dist = rnd.uniform(70, 400)
    x, y = CX + cos(ang) * dist, CY + sin(ang) * dist
    o = bpy.data.objects.new('blk', block_mesh)
    o.location = (x, y, G)
    o.scale = (rnd.uniform(40, 90), 13, rnd.uniform(28, 40))
    o.rotation_euler = (0, 0, rnd.choice((0, 1.57)) + rnd.uniform(-0.15, 0.15))
    sc.collection.objects.link(o)
for i in range(300):
    ang = rnd.uniform(pi * 1.05, pi * 1.95)
    dist = rnd.uniform(30, 600)
    tree(CX + cos(ang) * dist, CY + sin(ang) * dist, G, rnd.uniform(2.6, 4.5))

# ---------------------------------------------------------------- sky, sun, camera
world = bpy.data.worlds.new('World')
sc.world = world
world.use_nodes = True
nt = world.node_tree
sky = nt.nodes.new('ShaderNodeTexSky')
sky.sky_type = 'NISHITA'
sky.sun_disc = False
sky.sun_elevation = radians(26)
sky.altitude = 120
sky.air_density = 1.2
sky.dust_density = 1.6
nt.links.new(sky.outputs['Color'], nt.nodes['Background'].inputs['Color'])
nt.nodes['Background'].inputs['Strength'].default_value = 1.0
sun = bpy.data.lights.new('Sun', 'SUN')
sun.energy = 45.0
sun.angle = radians(0.8)
sun.color = (1.0, 0.86, 0.70)
so = bpy.data.objects.new('Sun', sun)
sc.collection.objects.link(so)
el, az = radians(26), radians(-6)
d = Vector((sin(az) * cos(el), cos(az) * cos(el), sin(el)))
so.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()

cam = bpy.data.cameras.new('pano')
cam.type = 'PANO'
cam.panorama_type = 'EQUIRECTANGULAR'
cam.clip_start = 0.05
cam.clip_end = 30000
co = bpy.data.objects.new('pano', cam)
co.location = (CX, CY, 1.6)
co.rotation_euler = (pi / 2, 0, 0)       # image centre looks to +Y (plan north, the river)
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
sc.view_settings.exposure = float(os.environ.get('PANO_EXP', '-3.6'))
sc.render.image_settings.file_format = 'JPEG'
sc.render.image_settings.quality = 88
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print('PANORAMA OK', OUT)
