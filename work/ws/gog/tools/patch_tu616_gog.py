#!/usr/bin/env python3
"""patch_tu616_gog.py - B274 (work/ws/b274_tu616/patch_tu616.py) for exes that are not the B274 input 2b7ee74c (GOG).

Same change and the same safety checks as patch_tu616.py, without its input-md5 gate: the ledge band test's "floor
below the ledge" constant at VA 0x85e4ac goes from the retail -628.9395 to the title update's -616.2975 (bytes
c41d3c21 -> c41a130a, exactly the TU float), only if:
  * the 4 bytes at 0x85e4ac are the retail value,
  * the only absolute references to 0x85e4ac in the file are the two `fcomp dword [0x85e4ac]` of 0x7260b0
    (0x726354 / 0x7263eb).
Anything else -> nothing is written.

Tested input: the GOG tru.exe (md5 76b4da2f...) after scripts/build_exe.sh (LAA + fmod / lighttex / soundplex guards).

  python -I work/ws/gog/tools/patch_tu616_gog.py IN.exe OUT.exe
"""
import hashlib, os, re, struct, sys

if len(sys.argv) != 3: sys.exit(__doc__)
src, dst = sys.argv[1:]
if os.path.abspath(src) == os.path.abspath(dst): sys.exit('refused: OUT is the input')
d = bytearray(open(src, 'rb').read())
pe = struct.unpack_from('<I', d, 0x3c)[0]; ns = struct.unpack_from('<H', d, pe + 6)[0]; so = struct.unpack_from('<H', d, pe + 20)[0]
ib = struct.unpack_from('<I', d, pe + 0x34)[0]


def off(va):
    for i in range(ns):
        e = pe + 24 + so + 40 * i; vs, vaa, rs, ro = struct.unpack_from('<IIII', d, e + 8)
        if ib + vaa <= va < ib + vaa + max(vs, rs): return ro + va - ib - vaa
    sys.exit('VA %#x not in the file' % va)


VA = 0x85e4ac
OLD, NEW = struct.pack('<f', -628.9395141601562), struct.pack('<f', -616.2974853515625)
o = off(VA)
if bytes(d[o:o + 4]) == NEW: sys.exit('already patched (TU value present) - nothing written')
if bytes(d[o:o + 4]) != OLD: sys.exit('refused: bytes at 0x85e4ac are %s, not the retail value' % bytes(d[o:o + 4]).hex())
refs = [m.start() for m in re.finditer(re.escape(struct.pack('<I', VA)), bytes(d))]
sites = sorted(off(v) for v in (0x726354 + 2, 0x7263eb + 2))
if refs != sites: sys.exit('refused: references to 0x85e4ac at %s, expected only %s' % ([hex(r) for r in refs], [hex(s) for s in sites]))
for v in (0x726354, 0x7263eb):
    if bytes(d[off(v):off(v) + 2]) != b'\xd8\x1d': sys.exit('refused: no fcomp at %#x' % v)
d[o:o + 4] = NEW
open(dst, 'wb').write(d)
print('%s  md5 %s  (in md5 %s)' % (dst, hashlib.md5(d).hexdigest(), hashlib.md5(open(src, 'rb').read()).hexdigest()))
