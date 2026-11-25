"""tg_runtime.py - (19/11/2026) solo lettura di un dump completo: blocchi dati dei terrain group di machine_room (DTP 25392 +0x221b0,
0x30 B) in memoria, e le strutture TerrainGroup (0x50 B) che li puntano a +0x30 (Lukas ENGINE.md: NtTerrainGroup resolve).
uso: python -I -B tg_runtime.py DUMP"""
import sys, struct, re
sys.path.insert(0, '/path/to/trudlcport/tools')
from minidump_read import Minidump
D = Minidump(sys.argv[1])
def rd(va, n):
    for v, sz, off in D.ranges:
        if v <= va and va + n <= v + sz: return D.d[off + va - v:off + va - v + n]
def find_all(pat):
    out = []
    for v, sz, off in D.ranges:
        blob = D.d[off:off + sz]
        for m in re.finditer(re.escape(pat), blob): out.append(v + m.start())
    return out
# blocco del gruppo 12 (maschera 0x4000): +0x10 float 75,100,20 ... +0x24 = 0x4000
sig = bytes.fromhex('000096420000c8420000a04100000000000000000040000000000000')
hits = find_all(sig)
print('blocchi gruppo 12 in memoria:', [hex(h - 0x10) for h in hits])
for h in hits:
    b12 = h - 0x10; base = b12 - 12 * 0x30
    recs = [base + g * 0x30 for g in range(29)]
    ptr = {}
    for g, r in enumerate(recs):
        for a in find_all(struct.pack('<I', r)): ptr.setdefault(g, []).append(a)
    print('base blocchi', hex(base))
    for g in range(29):
        rec = rd(recs[g], 0x30); msk = struct.unpack_from('<I', rec, 0x24)[0]
        for a in ptr.get(g, []):
            tg = a - 0x30; s = rd(tg, 0x50)
            if s is None: continue
            w = struct.unpack('<20I', s)
            print('g%2d mask %6x  tg %08x  ' % (g, msk, tg) + ' '.join('%08x' % x for x in w))
