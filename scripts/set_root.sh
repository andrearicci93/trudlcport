#!/bin/bash
# The scripts were written with the original working directory hard-coded. This rewrites the placeholder
# /path/to/trudlcport (and the other /path/to/... placeholders you choose) to your real paths, in place.
#   usage: scripts/set_root.sh            # sets /path/to/trudlcport -> this checkout
HERE=$(cd "$(dirname "$0")/.." && pwd)
grep -rIl "/path/to/trudlcport" "$HERE/tools" "$HERE/work" | while read f; do
  python3 - "$f" "$HERE" <<'PY'
import sys
p, root = sys.argv[1:3]
s = open(p, encoding='utf-8', errors='surrogateescape').read().replace('/path/to/trudlcport', root)
open(p, 'w', encoding='utf-8', errors='surrogateescape').write(s)
PY
done
echo "root set to $HERE"
echo "Other placeholders (/path/to/TombRaiderUnderworld_Patched, /path/to/Xenia-SteveRepack, ...) point at YOUR copies of the Xbox 360 files: grep -rn '/path/to/' tools work"
