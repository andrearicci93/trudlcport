#!/bin/bash
# B90_gold = B88b_acqua + giro6/tree SENZA i 3 DRM L2 (dlc_level1_start, dlc_dungeon, dlc_dungeonhallb). Opz. $1 = c100w K -> aggiunge L4 (variante webdim).
set -e
R=/path/to/trudlcport/work; D=$R/ws/giro7/compose$2/mods
rm -rf "$D"; mkdir -p "$(dirname "$D")"; cp -cR $R/baseline/B88b_acqua/mods "$D"; chmod -R u+w "$D"
(cd $R/ws/giro6/tree && find . -type f | while read f; do
  case "$f" in ./dlc_level1_start.drm|./dlc_dungeon.drm|./dlc_dungeonhallb.drm) continue;; esac
  mkdir -p "$D/$(dirname "$f")"; cp -f "$f" "$D/$f"; done)
if [ -n "$1" ]; then FIELDARG=${3:-c100w}
  T=$R/ws/giro7/l4tmp$2; rm -rf $T
  /path/to/trudlcport/tools/venv/bin/python -I $R/ws/giro6/l4_webs.py "$D" $T $1 $FIELDARG
  (cd $T && find . -type f -name '*.drm' | while read f; do cp -f "$f" "$D/$f"; done)
fi
echo composto $D
