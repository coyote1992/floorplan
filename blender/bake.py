"""Lightmap bake + glTF export.
   FLAT=<id> blender -b build/<id>/flat.blend -P blender/bake.py -- [--rooms living,bedroom] [--samples 128] [--skip-bake]
Outputs assets/<id>/flat.glb, assets/<id>/lm_<room>.jpg and updates data/<id>.json."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import bmesh
import json
import math
import time
import numpy as np
from math import radians
from plan import ROOMS, FLAT
import plan as flat

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, 'assets', FLAT)
LMDIR = os.path.join(ROOT, 'build', FLAT, 'lightmaps')
os.makedirs(ASSETS, exist_ok=True)
os.makedirs(LMDIR, exist_ok=True)

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []


def arg(name, default=None):
    if name in argv:
        i = argv.index(name)
        return argv[i + 1] if i + 1 < len(argv) and not argv[i + 1].startswith('--') else True
    return default


SAMPLES = int(arg('--samples', 128))
ROOMS_TO_BAKE = arg('--rooms', None)
SKIP_BAKE = bool(arg('--skip-bake', False))
SIZES = {k: (2048 if flat.room_area(k) > 8 else 1536 if flat.room_area(k) > 3.5 else 1024) for k in ROOMS}
SIZES.update(getattr(flat, 'LM_SIZES', {}))
ARCH_DENSITY = 2.5   # texel density multiplier for walls / floors / ceilings
LM_MAX = 6.0          # irradiance mapped to 1.0 in the 8-bit lightmaps (sRGB encoded)

sc = bpy.context.scene
vl = bpy.context.view_layer


def group(room):
    return [o for o in bpy.data.objects if o.type == 'MESH' and o.get('room') == room and o.get('lightmap') and not o.get('lm_own')]


def own_uv(o):
    """Generated pieces (thousands of small faces) bake into their own lightmap laid out like their texture,
    instead of being cut into tiny islands of the room's atlas."""
    me = o.data
    if 'Lightmap' not in me.uv_layers:
        me.uv_layers.active = me.uv_layers[0]
        me.uv_layers.new(name='Lightmap', do_init=True)
    me.uv_layers[0].active_render = True
    o['lmkey'] = o.name


# ---------------------------------------------------------------- lightmap UVs
def make_lightmap_uvs(objs, margin):
    for o in objs:
        me = o.data
        if me.users > 1:
            o.data = me.copy()
            me = o.data
        if 'Lightmap' not in me.uv_layers:
            if 'UVMap' not in me.uv_layers:
                me.uv_layers.new(name='UVMap')
            me.uv_layers.new(name='Lightmap')
        me.uv_layers['UVMap'].active_render = True
        me.uv_layers.active = me.uv_layers['Lightmap']
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    vl.objects.active = objs[0]
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=radians(55), island_margin=0.0, area_weight=0.0,
                             correct_aspect=True, scale_to_bounds=False)
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.average_islands_scale()
    bpy.ops.object.mode_set(mode='OBJECT')
    # big architectural surfaces get more texels than small furniture parts (sun patches, soft shadows)
    for o in objs:
        k = 1.0
        kind = o.get('kind')
        if kind in ('floor', 'wall', 'ceiling') or o.name.startswith(('tiles_', 'skirting_')):
            k = ARCH_DENSITY
        elif sum(o.dimensions) < 0.6:
            k = 0.6
        if k != 1.0:
            uv = o.data.uv_layers['Lightmap'].data
            co = [0.0] * (len(uv) * 2)
            uv.foreach_get('uv', co)
            uv.foreach_set('uv', [c * k for c in co])
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.pack_islands(rotate=True, margin=margin, scale=True)
    bpy.ops.object.mode_set(mode='OBJECT')
    for o in objs:
        o.data.uv_layers.active = o.data.uv_layers['UVMap']


# ---------------------------------------------------------------- bake
def bake_group(room, objs, size):
    img = bpy.data.images.new('LM_' + room, size, size, float_buffer=True, alpha=False)
    img.colorspace_settings.name = 'Linear Rec.709'
    mats = set()
    for o in objs:
        for s in o.material_slots:
            if s.material:
                mats.add(s.material)
    for m in mats:
        nt = m.node_tree
        n = nt.nodes.get('LM_BAKE') or nt.nodes.new('ShaderNodeTexImage')
        n.name = 'LM_BAKE'
        n.image = img
        n.location = (-1200, -600)
        for nn in nt.nodes:
            nn.select = False
        n.select = True
        nt.nodes.active = n
        uvn = nt.nodes.get('LM_UV') or nt.nodes.new('ShaderNodeUVMap')
        uvn.name = 'LM_UV'
        uvn.uv_map = 'Lightmap'
        if not n.inputs['Vector'].links:
            nt.links.new(uvn.outputs['UV'], n.inputs['Vector'])
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
        o.data.uv_layers.active = o.data.uv_layers['Lightmap']     # Cycles bakes into the active UV map
    vl.objects.active = objs[0]
    sc.render.bake.use_pass_direct = True
    sc.render.bake.use_pass_indirect = True
    sc.render.bake.use_pass_color = False
    sc.render.bake.margin = 6
    sc.render.bake.margin_type = 'EXTEND'
    sc.render.bake.target = 'IMAGE_TEXTURES'
    sc.cycles.samples = SAMPLES
    t0 = time.time()
    bpy.ops.object.bake(type='DIFFUSE', pass_filter={'DIRECT', 'INDIRECT'}, use_clear=True, margin=6)
    print(f'BAKED {room} {size}px {SAMPLES} spp in {time.time() - t0:.0f}s', flush=True)
    for o in objs:
        o.data.uv_layers.active = o.data.uv_layers['UVMap']
    path = os.path.join(LMDIR, f'lm_{room}.exr')
    img.filepath_raw = path
    img.file_format = 'OPEN_EXR'
    img.save()
    return img, path


def denoise(path, size):
    """Run OIDN through the compositor on a baked EXR."""
    s2 = bpy.data.scenes.new('denoise')
    s2.render.resolution_x = s2.render.resolution_y = size
    s2.render.resolution_percentage = 100
    s2.render.engine = 'BLENDER_WORKBENCH'
    cam = bpy.data.objects.new('dn_cam', bpy.data.cameras.new('dn_cam'))
    s2.collection.objects.link(cam)
    s2.camera = cam
    s2.use_nodes = True
    nt = s2.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    im = bpy.data.images.load(path, check_existing=False)
    a = nt.nodes.new('CompositorNodeImage')
    a.image = im
    d = nt.nodes.new('CompositorNodeDenoise')
    d.use_hdr = True
    d.prefilter = 'NONE'
    c = nt.nodes.new('CompositorNodeComposite')
    nt.links.new(a.outputs['Image'], d.inputs['Image'])
    nt.links.new(d.outputs['Image'], c.inputs['Image'])
    s2.render.image_settings.file_format = 'OPEN_EXR'
    s2.render.image_settings.color_depth = '32'
    s2.view_settings.view_transform = 'Standard'
    out = path.replace('.exr', '_dn.exr')
    s2.render.filepath = out
    with bpy.context.temp_override(scene=s2):
        bpy.ops.render.render(write_still=True, scene=s2.name)
    bpy.data.scenes.remove(s2)
    return out


def encode(path_exr, room):
    im = bpy.data.images.load(path_exr, check_existing=False)
    w, h = im.size
    a = np.empty(w * h * 4, np.float32)
    im.pixels.foreach_get(a)
    a = a.reshape(h, w, 4)[:, :, :3]
    x = np.clip(a / LM_MAX, 0, 1)
    enc = np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(x, 1 / 2.4) - 0.055)
    out = bpy.data.images.new('enc_' + room, w, h, alpha=False)
    out.colorspace_settings.name = 'Non-Color'
    px = np.ones((h, w, 4), np.float32)
    px[:, :, :3] = enc
    out.pixels.foreach_set(px.ravel())
    p = os.path.join(ASSETS, f'lm_{room}.jpg')
    out.filepath_raw = p
    out.file_format = 'JPEG'
    sc.render.image_settings.quality = 92
    out.save()
    stats = dict(p50=float(np.percentile(a, 50)), p99=float(np.percentile(a, 99)), max=float(a.max()))
    print('ENCODED', room, stats, flush=True)
    return stats


# ---------------------------------------------------------------- main
sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
for o in bpy.data.objects:
    if o.type == 'MESH' and o.get('lightmap') is None:
        o['lightmap'] = False

# pieces you can move in the viewer stay out of the baked light (no shadow left behind when they move)
movable = [o for o in bpy.data.objects if o.get('dynamic')]
for o in movable:
    o.hide_render = True

rooms = list(ROOMS.keys()) if not ROOMS_TO_BAKE else ROOMS_TO_BAKE.split(',')
info = {}
for room in rooms:
    objs = group(room)
    if not objs:
        continue
    size = SIZES.get(room, 1024)
    make_lightmap_uvs(objs, margin=6 / size * 1.6)
    if SKIP_BAKE:
        continue
    img, p = bake_group(room, objs, size)
    try:
        p = denoise(p, size)
    except Exception as e:  # keep the raw bake if the compositor is unavailable
        print('DENOISE FAILED', room, e, flush=True)
    info[room] = encode(p, room)

# generated pieces with a lightmap of their own (size in their 'lm_own' property)
for o in [o for o in bpy.data.objects if o.type == 'MESH' and o.get('lightmap') and o.get('lm_own')]:
    own_uv(o)
    if o.get('room') not in rooms or SKIP_BAKE:
        continue
    size = int(o['lm_own'])
    img, p = bake_group(o.name, [o], size)
    try:
        p = denoise(p, size)
    except Exception as e:
        print('DENOISE FAILED', o.name, e, flush=True)
    info[o.name] = encode(p, o.name)

# objects of rooms that were not re-baked keep their previous UVs: make sure every lightmapped object has a Lightmap UV
for room in ROOMS:
    if room in rooms:
        continue
    objs = group(room)
    if objs and any('Lightmap' not in o.data.uv_layers for o in objs):
        make_lightmap_uvs(objs, margin=6 / SIZES.get(room, 1024) * 1.6)

for o in movable:
    o.hide_render = False

# remove bake helper nodes so they are not exported
for m in bpy.data.materials:
    if m.node_tree:
        for nm in ('LM_BAKE', 'LM_UV'):
            n = m.node_tree.nodes.get(nm)
            if n:
                m.node_tree.nodes.remove(n)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, 'build', FLAT, 'flat_baked.blend'))

# ---------------------------------------------------------------- export
for o in bpy.data.objects:
    o.select_set(o.type == 'MESH')
bpy.ops.export_scene.gltf(
    filepath=os.path.join(ASSETS, 'flat.glb'), export_format='GLB', use_selection=True,
    export_apply=True, export_texcoords=True, export_normals=True, export_tangents=False,
    export_materials='EXPORT', export_image_format='AUTO', export_image_quality=85,
    export_extras=True, export_cameras=False, export_lights=False, export_yup=True,
    export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=6,
    export_draco_position_quantization=14, export_draco_normal_quantization=10,
    export_draco_texcoord_quantization=16, export_draco_generic_quantization=12)

sj = os.path.join(ROOT, 'data', f'{FLAT}.json')
data = json.load(open(sj))
lm = data.get('lightmaps', {})
for r in list(ROOMS) + [o.name for o in bpy.data.objects if o.get('lm_own')]:
    if os.path.exists(os.path.join(ASSETS, f'lm_{r}.jpg')):
        lm[r] = dict(file=f'assets/{FLAT}/lm_{r}.jpg', **{k: v for k, v in (info.get(r) or lm.get(r, {})).items() if k != 'file'})
data['lightmaps'] = lm
data['lmMax'] = LM_MAX
json.dump(data, open(sj, 'w'), indent=1)
print('EXPORT OK', flush=True)
