"""B274: soglia «pavimento sotto il ledge» del test di fascia 0x7260b0 come la TU Xbox.
Base Xbox (FUN_8241d148, costante 0x8207df68) e PC (0x85e4ac) = -628.9395; TU (FUN_824201d8, costante 0x8207e7d8) = -616.2975.
Il test (record di tipo 3/4 della tabella classi del ledge) chiede quota_colpita - quota_ledge <= costante. Caso goo_room: ledge sotto la
vena 196acdc0 con la pozza di eitr a -625.9 -> PC scarta (classe 3), Xbox/TU accetta (classe 0). Usi della costante nel PC: solo
0x726356 e 0x7263ed (fcomp dword [0x85e4ac]), entrambi in 0x7260b0.
uso: patch_tu616.py IN.exe OUT.exe   (IN = 2b7ee74c)"""
import sys, struct, hashlib, re
d = bytearray(open(sys.argv[1], 'rb').read())
assert hashlib.md5(d).hexdigest() == '2b7ee74c37394be208195efd0952cd5f', hashlib.md5(d).hexdigest()
pe = struct.unpack_from('<I', d, 0x3c)[0]; ns = struct.unpack_from('<H', d, pe + 6)[0]; so = struct.unpack_from('<H', d, pe + 20)[0]
ib = struct.unpack_from('<I', d, pe + 0x34)[0]
def off(va):
    for i in range(ns):
        e = pe + 24 + so + 40 * i; vs, vaa, rs, ro = struct.unpack_from('<IIII', d, e + 8)
        if ib + vaa <= va < ib + vaa + max(vs, rs): return ro + va - ib - vaa
VA = 0x85e4ac
OLD, NEW = struct.pack('<f', -628.9395141601562), struct.pack('<f', -616.2974853515625)
o = off(VA); assert bytes(d[o:o + 4]) == OLD, bytes(d[o:o + 4]).hex()
# riferimenti assoluti alla costante: devono essere solo i due fcomp di 0x7260b0
refs = [m.start() for m in re.finditer(re.escape(struct.pack('<I', VA)), bytes(d))]
sites = sorted(off(v) for v in (0x726354 + 2, 0x7263eb + 2))
assert refs == sites, ([hex(r) for r in refs], [hex(s) for s in sites])
for v in (0x726354, 0x7263eb): assert bytes(d[off(v):off(v) + 2]) == b'\xd8\x1d', hex(v)   # fcomp dword ptr [abs]
d[o:o + 4] = NEW
open(sys.argv[2], 'wb').write(d); print(sys.argv[2], hashlib.md5(d).hexdigest())
