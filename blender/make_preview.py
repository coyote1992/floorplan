"""Assemble a self-contained preview folder (build/preview/) from the site:
the page without its document shell, plus every file it loads. Uses the separate-file glTF export
(no WebAssembly decoder needed).  python3 blender/make_preview.py"""
import json
import os
import re
import shutil

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

files = ['app.js', 'vendor/three/three.module.min.js', 'vendor/three/addons/loaders/GLTFLoader.js',
         'vendor/three/addons/loaders/DRACOLoader.js', 'vendor/three/addons/controls/OrbitControls.js',
         'vendor/three/addons/utils/BufferGeometryUtils.js', 'assets/view.jpg']
data = json.load(open(os.path.join(ROOT, 'data', 'scene.json')))
for lm in data.get('lightmaps', {}).values():
    files.append(lm['file'])
web = os.path.join(ROOT, 'build', 'web_gltf')
for dp, _, fns in os.walk(web):
    for fn in fns:
        rel = os.path.relpath(os.path.join(dp, fn), web)
        dst = os.path.join(OUT, 'assets', 'web', rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy(os.path.join(dp, fn), dst)
# artifact hosting serves neither .gltf nor .bin: inline the geometry buffer and keep the JSON as .json
import base64
gpath = os.path.join(OUT, 'assets', 'web', 'flat.gltf')
g = json.load(open(gpath))
for buf in g['buffers']:
    if buf.get('uri') and not buf['uri'].startswith('data:'):
        bp = os.path.join(OUT, 'assets', 'web', buf['uri'])
        buf['uri'] = 'data:application/octet-stream;base64,' + base64.b64encode(open(bp, 'rb').read()).decode()
        os.remove(bp)
json.dump(g, open(os.path.join(OUT, 'assets', 'web', 'flat.json'), 'w'), separators=(',', ':'))
os.remove(gpath)
data['model'] = 'assets/web/flat.json'
data['modelBytes'] = os.path.getsize(os.path.join(OUT, 'assets', 'web', 'flat.json'))
os.makedirs(os.path.join(OUT, 'data'))
json.dump(data, open(os.path.join(OUT, 'data', 'scene.json'), 'w'))
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
