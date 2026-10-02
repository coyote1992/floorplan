#!/usr/bin/env bash
# Download the CC0 source assets used by the Blender build (not stored in git).
#   ambientCG materials  -> assets_src/tex/<id>/
#   Poly Haven models    -> assets_src/models/<id>/
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p assets_src/tex assets_src/models

acg() {  # id resolution
  local id=$1 res=$2
  [ -d "assets_src/tex/$id" ] && return
  curl -sSL -o "assets_src/tex/$id.zip" "https://ambientcg.com/get?file=${id}_${res}-JPG.zip"
  mkdir -p "assets_src/tex/$id" && unzip -q -o "assets_src/tex/$id.zip" -d "assets_src/tex/$id" && rm "assets_src/tex/$id.zip"
  find "assets_src/tex/$id" \( -name '*.blend' -o -name '*.usdc' -o -name '*.mtlx' -o -name '*.tres' \
       -o -name '*Displacement*' -o -name '*NormalDX*' -o -name '*.png' \) -delete
}
for id in WoodFloor051 Tiles141 Tiles139; do acg "$id" 2K; done
for id in Fabric023 Fabric030 Fabric062 Fabric036 Wood092 Wood048 Wood049 Wood058 Wood052 Wood068 Wood028 Marble014; do acg "$id" 1K; done

ph() {  # Poly Haven glTF at 1k
  local id=$1
  [ -d "assets_src/models/$id" ] && return
  python3 - "$id" <<'EOF'
import json, os, subprocess, sys, urllib.request
mid = sys.argv[1]
info = json.load(urllib.request.urlopen(f'https://api.polyhaven.com/files/{mid}'))
g = info['gltf']['1k']['gltf']
d = os.path.join('assets_src', 'models', mid)
jobs = [(g['url'], os.path.join(d, os.path.basename(g['url'])))]
jobs += [(v['url'], os.path.join(d, k)) for k, v in g.get('include', {}).items()]
for url, path in jobs:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    subprocess.run(['curl', '-sSL', '-o', path, url], check=True)
print(mid, 'ok')
EOF
}
for id in pachira_aquatica_01 potted_plant_02 potted_plant_04 calathea_orbifolia_01 ceramic_vase_01 ceramic_vase_03; do ph "$id"; done
echo "assets ready"
