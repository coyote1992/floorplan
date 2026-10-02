"""Re-export the baked flat without re-baking.
   blender -b build/flat_baked.blend -P blender/export.py -- [--separate] [--no-draco] [--out assets/flat.glb]
--separate writes .gltf + .bin + image files (each file small, no WebAssembly decoder needed)."""
import sys
import os
import bpy

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
separate = '--separate' in argv
draco = '--no-draco' not in argv and not separate
out = argv[argv.index('--out') + 1] if '--out' in argv else os.path.join(ROOT, 'assets', 'flat.gltf' if separate else 'flat.glb')
out = os.path.abspath(out)
os.makedirs(os.path.dirname(out), exist_ok=True)

for o in bpy.data.objects:
    o.select_set(o.type == 'MESH')
kw = dict(filepath=out, export_format='GLTF_SEPARATE' if separate else 'GLB', use_selection=True,
          export_apply=True, export_texcoords=True, export_normals=True, export_tangents=False,
          export_materials='EXPORT', export_image_format='AUTO', export_image_quality=85,
          export_extras=True, export_cameras=False, export_lights=False, export_yup=True)
if separate:
    kw['export_texture_dir'] = 'tex'
if draco:
    kw.update(export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=6,
              export_draco_position_quantization=14, export_draco_normal_quantization=10,
              export_draco_texcoord_quantization=16, export_draco_generic_quantization=12)
bpy.ops.export_scene.gltf(**kw)
print('EXPORTED', out)
