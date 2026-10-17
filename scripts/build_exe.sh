#!/bin/bash
# Build the patched game executable from the Steamless-UNPACKED tru.exe.
#   usage: scripts/build_exe.sh UNPACKED_TRU.exe OUT.exe
# Chain: LAA flag -> fmod_init_guard -> light_tex_guard -> soundplex_guard.
# With the reference unpack (md5 56d1ce2dffa62f16354063da2df44d5a) the result is md5 f47814ff116a4a33842bdb846bf97982.
set -e
IN=$1; OUT=$2; HERE=$(cd "$(dirname "$0")/.." && pwd); PY=${PY:-python3}; T=$(mktemp -d)
$PY "$HERE/scripts/make_laa.py" "$IN" "$T/laa.exe"
$PY "$HERE/tools/fmod_init_guard.py" "$T/laa.exe" "$T/a.exe" | tail -1
$PY "$HERE/tools/light_tex_guard.py" "$T/a.exe" "$T/b.exe" | tail -1
$PY "$HERE/tools/soundplex_guard.py" "$T/b.exe" "$OUT" | tail -1
md5sum "$OUT" 2>/dev/null || md5 "$OUT"
rm -rf "$T"
