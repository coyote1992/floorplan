"""Assemble a self-contained preview folder (build/preview/) from the site:
the page without its document shell, plus every file it loads. Uses the separate-file glTF export
(no WebAssembly decoder needed), for every flat in data/flats.json.  python3 blender/make_preview.py"""
import json
import os
import re
import shutil
import base64

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'build', 'preview')
shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(OUT)

html = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
head = re.search(r'<head>(.*)</head>', html, re.S).group(1)
body = re.search(r'<body>(.*)</body>', html, re.S).group(1)
head = re.sub(r'<meta charset[^>]*>\s*', '', head)
head = re.sub(r'<meta name="viewport"[^>]*>\s*', '', head)
open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(head.strip() + '\n' + body.strip() + '\n')

files = ['app.js', 'data/flats.json', 'vendor/three/three.module.min.js', 'vendor/three/addons/loaders/GLTFLoader.js',
         'vendor/three/addons/loaders/DRACOLoader.js', 'vendor/three/addons/controls/OrbitControls.js',
         'vendor/three/addons/utils/BufferGeometryUtils.js']
os.makedirs(os.path.join(OUT, 'data'))
# each flat: FLAT=<id> blender -b build/<id>/flat_baked.blend -P blender/export.py -- --separate --out build/<id>/web_gltf/flat.gltf
for flat in json.load(open(os.path.join(ROOT, 'data', 'flats.json')))['flats']:
    fid = flat['id']
    data = json.load(open(os.path.join(ROOT, flat['data'])))
    files.append(data['view'])
    for lm in data.get('lightmaps', {}).values():
        files.append(lm['file'])
    web = os.path.join(ROOT, 'build', fid, 'web_gltf')
    dst_web = os.path.join(OUT, 'assets', fid, 'web')
    for dp, _, fns in os.walk(web):
        for fn in fns:
            dst = os.path.join(dst_web, os.path.relpath(os.path.join(dp, fn), web))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy(os.path.join(dp, fn), dst)
    # artifact hosting serves neither .gltf nor .bin: inline the geometry buffer and keep the JSON as .json
    gpath = os.path.join(dst_web, 'flat.gltf')
    g = json.load(open(gpath))
    for buf in g['buffers']:
        if buf.get('uri') and not buf['uri'].startswith('data:'):
            bp = os.path.join(dst_web, buf['uri'])
            buf['uri'] = 'data:application/octet-stream;base64,' + base64.b64encode(open(bp, 'rb').read()).decode()
            os.remove(bp)
    json.dump(g, open(os.path.join(dst_web, 'flat.json'), 'w'), separators=(',', ':'))
    os.remove(gpath)
    data['model'] = f'assets/{fid}/web/flat.json'
    data['modelBytes'] = os.path.getsize(os.path.join(dst_web, 'flat.json'))
    json.dump(data, open(os.path.join(OUT, flat['data']), 'w'))
for f in files:
    dst = os.path.join(OUT, f)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy(os.path.join(ROOT, f), dst)
total = 0
for dp, _, fns in os.walk(OUT):
    for fn in fns:
        p = os.path.join(dp, fn)
        total += os.path.getsize(p)
        if os.path.getsize(p) > 15e6:
            print('TOO BIG', p, os.path.getsize(p))
print('preview ready', OUT, round(total / 1e6, 1), 'MB')
