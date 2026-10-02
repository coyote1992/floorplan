"""Quick Cycles renders of the built flat for checking.  blender -b build/flat.blend -P blender/render_test.py -- [names]"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from math import radians, pi
from plan import X, Y, SPAWNS, H

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'build', 'renders')
os.makedirs(out, exist_ok=True)
sc = bpy.context.scene
samples = int(os.environ.get('SAMPLES', '48'))
sc.cycles.samples = samples
if os.environ.get('SUN'):
    bpy.data.objects['Sun'].data.energy = float(os.environ['SUN'])
if os.environ.get('SKY'):
    sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value = float(os.environ['SKY'])
TAG = os.environ.get('TAG', '')
if os.environ.get('NOGLASS'):
    for o in bpy.data.objects:
        if o.name.startswith('window_'):
            o.visible_shadow = False
sc.render.resolution_x = int(os.environ.get('RESX', '960'))
sc.render.resolution_y = int(os.environ.get('RESY', '600'))

VIEWS = {k: (v[0], v[1], v[2], 1.60, -0.42 if k in ('bath', 'wc') else 0.0) for k, v in SPAWNS.items()}
VIEWS.update({
    'living_b': (500, 130, 2.45, 1.60, -0.05),     # from the window corner towards the dining area
    'living_c': (300, 140, -2.35, 1.55, -0.05),    # from the armchair corner towards the sofa
    'bedroom_b': (150, 160, 3.14, 1.60, -0.08),    # from the window towards the door
    'hall_b': (300, 455, -1.0, 1.60, -0.05),
    'kitchen_b': (120, 650, -1.5708, 1.55, -0.12),
    'win_close': (397, 160, 0.0, 1.45, 0.0),
})


def cam(name, px, py, yaw, z=1.6, pitch=0.0, lens=16):
    c = bpy.data.cameras.new(name)
    c.lens = lens
    c.sensor_width = 36
    o = bpy.data.objects.new(name, c)
    sc.collection.objects.link(o)
    o.location = (X(px), Y(py), z)
    o.rotation_euler = (pi / 2 + pitch, 0, yaw)
    return o


names = argv or list(VIEWS.keys()) + ['overview']
for n in names:
    if n == 'overview':
        for o in bpy.data.objects:
            if o.get('kind') in ('ceiling',) or o.name.startswith('walls_top'):
                o.hide_render = True
        c = bpy.data.cameras.new('ov')
        c.type = 'ORTHO'
        c.ortho_scale = 11.5
        o = bpy.data.objects.new('ov', c)
        sc.collection.objects.link(o)
        o.location = (X(312), Y(377), 20)
        o.rotation_euler = (0, 0, 0)
        sc.camera = o
        rx, ry = sc.render.resolution_x, sc.render.resolution_y
        sc.render.resolution_x, sc.render.resolution_y = 800, 1000
        sc.render.filepath = os.path.join(out, 'overview.png')
        bpy.ops.render.render(write_still=True)
        sc.render.resolution_x, sc.render.resolution_y = rx, ry
        for o in bpy.data.objects:
            o.hide_render = False
        continue
    v = VIEWS[n]
    sc.camera = cam('cam_' + n, v[0], v[1], v[2], v[3] if len(v) > 3 else 1.6, v[4] if len(v) > 4 else 0.0)
    sc.render.filepath = os.path.join(out, n + TAG + '.png')
    bpy.ops.render.render(write_still=True)
    print('RENDERED', n)
