#!/usr/bin/env bash
# Bake a flat one room per Blender run, so an interrupted bake picks up where it stopped: rerun the same command and
# rooms whose lightmap is newer than the start marker are skipped. The last run's export is the final flat.glb.
#   FLAT=garden blender/bake_rooms.sh [samples] [blender]
#   FLAT=garden blender/bake_rooms.sh --fresh     forget earlier progress and bake every room again
set -euo pipefail
cd "$(dirname "$0")/.."
FLAT=${FLAT:?set FLAT}
if [ "${1:-}" = "--fresh" ]; then rm -f "build/$FLAT/bake_started"; shift; fi
SAMPLES=${1:-128}
BLENDER=${2:-${BLENDER:-blender}}
MARK="build/$FLAT/bake_started"
[ -f "$MARK" ] || touch "$MARK"
ROOMS=$(python3 -c "import json; print(' '.join(r['id'] for r in json.load(open('data/$FLAT.json'))['rooms']))")
# the showcase room first
ROOMS="living $(echo "$ROOMS" | tr ' ' '\n' | grep -vx living | tr '\n' ' ')"
for r in $ROOMS; do
  if [ "assets/$FLAT/lm_$r.jpg" -nt "$MARK" ]; then echo "skip $r (done)"; continue; fi
  echo "bake $r"
  FLAT=$FLAT "$BLENDER" -b "build/$FLAT/flat.blend" -P blender/bake.py -- --samples "$SAMPLES" --rooms "$r" \
    > "build/$FLAT/bake_$r.log" 2>&1
  grep -E "BAKED|UVHASH|EXPORT OK|Traceback|Error" "build/$FLAT/bake_$r.log" | cut -c1-120
done
rm -f "$MARK"
echo "ALL ROOMS BAKED"
