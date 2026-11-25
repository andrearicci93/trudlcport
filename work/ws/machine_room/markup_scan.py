"""markup_scan.py - (20/11/2026) solo lettura. Record MarkUp dei modelli (DTP 0x04c20453, header +0x54 n, +0x58 -> record 0x5c B;
ENGINE.md del fork: +0x2e id, +0x33 tipo, +0x34 pos, +0x58 poligono). Regole dal base (model58_cmp.py, 83 modelli / 297 record):
+0x2c = coppia u16 {0, id} (s16; id rimappato nei modelli base), +0x30 = {s16 osso, u8, u8 tipo} (s16b2, raw se simmetrico),
+0x34..+0x54 = s32. Per ogni modello di ogni DRM DLC della baseline confronta con il sorgente Xbox e stampa le parole fuori regola.
uso: python -I -B markup_scan.py BASELINE"""
import sys, struct, collections
sys.path.insert(0, '/path/to/trudlcport/work/ws/lukas_check/inv'); sys.path.insert(0, '/path/to/trudlcport/tools')
import inv_common as C, drm_write as DW, drm_reloc as R
MAG = bytes.fromhex('04c20453'); ST = 0x5c
def want(o, x):
    if o == 0x2c: return x[1::-1] + x[:1:-1]
    if o == 0x30: return x[1::-1] + x[2:]
    if 0x34 <= o <= 0x54: return x[::-1]
    return None
im7 = C.idmap().get(7, {}); tot = collections.Counter(); rows = []
for rel, path in C.files(sys.argv[1]):
    xr = C.xbox(rel)
    if xr is None: continue
    X = DW.read(xr, 'be'); P = DW.read(open(path, 'rb').read(), 'le')
    pc = collections.defaultdict(list)
    for s in P.sections:
        if s.type == 7: pc[s.id].append(s)
    for x in X.sections:
        if x.type != 7 or bytes(x.data[:4]) != MAG: continue
        ps = [p for p in pc.get(im7.get(x.id, x.id), []) if len(p.data) == len(x.data)]
        if len(ps) != 1: tot['senza coppia'] += 1; continue
        p = ps[0]; r = R.parse(bytes(x.reloc), 'be'); it = dict(r.internal); T = it.get(0x58)
        if T is None: continue
        n = struct.unpack_from('>I', x.data, 0x54)[0]
        if not n or T + ST * n > len(x.data): continue
        sl = set(it) | {o for _, o in list(r.idref) + list(r.idref_a)}
        tot['modelli'] += 1; tot['record'] += n
        for k in range(n):
            for o in range(0x2c, 0x58, 4):
                a = T + ST * k + o
                if a in sl: continue
                xw, pw = bytes(x.data[a:a + 4]), bytes(p.data[a:a + 4]); w = want(o, xw)
                if pw == w: tot['ok'] += 1; continue
                if o == 0x2c and pw[:2] == b'\0\0' and xw[:2] == b'\0\0': tot['ok (id rimappato)'] += 1; continue
                tot['DIFETTO +%#x' % o] += 1
                rows.append('%-40s DTP %d rec %2d +%#04x xbox %s pc %s atteso %s' % (rel, p.id, k, o, xw.hex(), pw.hex(), w.hex()))
for l in rows: print(l)
print('totale', dict(tot))
