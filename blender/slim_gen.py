"""Slim a model generated with image-blaster (FAL Hunyuan3D) for the web, keeping where it came from.
   blender -b -P blender/slim_gen.py -- <world-output-dir> <flat> <id> <faces> <colour px> <data px> [gamma [gamma for saturated colours]]
Reads <world-output-dir>/<id>/0-<id>.glb (50k faces, 4096 px PBR maps) and writes gen/<flat>/<id>.glb
(decimated, maps resized) plus the cut-out reference image and a provenance note next to it.
gamma < 1 lifts a colour map that came out darker than the real piece (colour ** gamma); greys get the first
value and saturated colours the second (image-to-3D tends to sink neutral fabrics more than coloured ones)."""
import bpy
import json
import os
import sys

argv = sys.argv[sys.argv.index('--') + 1:]
src_dir, flat, oid, faces, tex, tex_data = argv[0], argv[1], argv[2], int(argv[3]), int(argv[4]), int(argv[5])
gamma = float(argv[6]) if len(argv) > 6 else 1.0
gamma_sat = float(argv[7]) if len(argv) > 7 else gamma
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'gen', flat)
os.makedirs(OUT, exist_ok=True)
obj_dir = os.path.join(src_dir, oid)
src = os.path.join(obj_dir, f'0-{oid}.glb')

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
assert len(meshes) == 1, meshes
ob = meshes[0]
n0 = len(ob.data.polygons)
if n0 > faces:
    m = ob.modifiers.new('decimate', 'DECIMATE')
    m.decimate_type = 'COLLAPSE'
    m.ratio = faces / n0
    m.use_collapse_triangulate = True
    with bpy.context.temp_override(object=ob, active_object=ob):
        bpy.ops.object.modifier_apply(modifier=m.name)
for im in bpy.data.images:
    colour = im.colorspace_settings.name == 'sRGB'
    size = tex if colour else tex_data
    if max(im.size) > size:
        im.scale(size, size)
    if colour and gamma != 1.0:
        import numpy as np
        px = np.empty(len(im.pixels), dtype=np.float32)
        im.pixels.foreach_get(px)
        px = px.reshape(-1, 4)
        rgb = np.clip(px[:, :3], 0, 1)
        w = np.clip((rgb.max(1) - rgb.min(1)) / 0.25, 0, 1)[:, None]      # 0 for greys, 1 for saturated colours
        px[:, :3] = rgb ** (gamma * (1 - w) + gamma_sat * w)
        im.pixels.foreach_set(px.ravel())
        im.update()
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, f'{oid}.glb'), export_format='GLB', export_image_format='JPEG',
                          export_image_quality=90, export_materials='EXPORT', export_yup=True)

# provenance: which photo crop, prompt and model request produced it
ref = os.path.join(obj_dir, f'0-{oid}.png')
if os.path.exists(ref):
    im = bpy.data.images.load(ref)
    sc = bpy.context.scene
    sc.render.image_settings.file_format = 'JPEG'
    sc.render.image_settings.quality = 88
    im.save_render(os.path.join(OUT, f'{oid}-reference.jpg'), scene=sc)
note = {'id': oid, 'faces_generated': n0, 'faces': len(ob.data.polygons), 'texture_px': [tex, tex_data], 'colour_gamma': [gamma, gamma_sat]}
for kind in ('image', 'model'):
    p = os.path.join(obj_dir, f'.0-{oid}__{kind}-request.json')
    if os.path.exists(p):
        r = json.load(open(p))
        note[kind] = {k: r.get(k) for k in ('endpoint', 'request_id', 'submitted_at', 'completed_at', 'prompt') if r.get(k)}
        inp = {k: v for k, v in (r.get('input') or {}).items() if not (isinstance(v, str) and len(v) > 300)}
        if inp:
            note[kind]['input'] = inp
obj = os.path.join(obj_dir, 'object.json')
if os.path.exists(obj):
    o = json.load(open(obj))['object']
    note['name'] = o.get('name')
    note['description'] = o.get('description')
    note['source_images'] = [os.path.basename(s) for s in o.get('source_images', [])]
json.dump(note, open(os.path.join(OUT, f'{oid}.json'), 'w'), indent=1)
print('SLIM', oid, n0, '->', len(ob.data.polygons), 'faces')
