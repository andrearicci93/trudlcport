#!/bin/bash
# compone mods completo = B88b_acqua + giro6/tree (cp -c: clone APFS)
set -e
R=/path/to/trudlcport/work
D=$R/ws/giro6/compose/mods
rm -rf "$D"; cp -cR $R/baseline/B88b_acqua/mods "$D"; chmod -R u+w "$D"
(cd $R/ws/giro6/tree && find . -type f | while read f; do mkdir -p "$D/$(dirname "$f")"; cp -f "$f" "$D/$f"; done)
echo composto $D
