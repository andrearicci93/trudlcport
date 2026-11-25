"""relayout_scan.py - (19/11/2026) solo lettura. Regola `fxrelayout` del fork di Lukas (logica riscritta): DTP «tabella di
record» = testa +0x34 u16 n (2..64), +0x38 puntatore P a n record; record Xbox 0x24 B {+0 u16u16, +4 u32 colore,
+8 u8u8u16, +0xc u16u16, +0x10 u16u16, +0x14 u32 id tipo 7, +0x18..0x23 zero}; sul PC il passo e' 0x28 (parola in piu' = 0).
Per ogni DTP cosi' fatto nella baseline dice se il PC ha passo 0x28 (ok), passo 0x24 (difetto) o altro, e se c'e' spazio
per riallinearlo (padding Xbox a zero, nessuna rilocazione dentro [P, P+0x28 n)).
uso: python -I -B relayout_scan.py BASELINE"""
import sys, os, struct, collections
sys.path.insert(0, '/path/to/trudlcport/work/ws/lukas_check/inv'); sys.path.insert(0, '/path/to/trudlcport/tools')
import inv_common as C, drm_write as DW, drm_reloc as R
XS, PS = 0x24, 0x28
LAY = {0x00: (1, 0, 3, 2), 0x04: (3, 2, 1, 0), 0x08: (0, 1, 3, 2), 0x0c: (1, 0, 3, 2), 0x10: (1, 0, 3, 2)}
im7 = C.idmap().get(7, {})
def table(x, xids):
    r = R.parse(bytes(x.reloc), 'be') if x.reloc else R.Reloc(); it = dict(r.internal); d = x.data
    if len(d) < 0x3c or 0x38 not in it: return None
    n = struct.unpack_from('>H', d, 0x34)[0]; P = it[0x38]
    if not (2 <= n <= 64 and P + XS * n <= len(d)): return None
    for j in range(n):
        q = P + XS * j
        if struct.unpack_from('>I', d, q + 0x14)[0] not in xids or d[q + 0x18:q + XS] != bytes(12): return None
    return n, P
def rec(d, q, pid):
    out = bytearray(PS)
    for w, pm in LAY.items(): out[w:w + 4] = bytes(d[q + w + i] for i in pm)
    struct.pack_into('<I', out, 0x14, pid); return bytes(out)
def room(x, n, P):
    r = R.parse(bytes(x.reloc), 'be') if x.reloc else R.Reloc(); lo, hi = P, P + PS * n
    if x.data[P + XS * n:hi] != bytes(hi - P - XS * n): return 'padding non zero'
    if any(lo <= o < hi for o, _ in r.internal) or any(lo < t < hi for _, t in r.internal): return 'puntatore dentro'
    if any(lo <= o < hi for _, o in list(r.idref) + list(r.idref_a)) or any(lo <= so < hi for _, so, _ in r.external): return 'riferimento dentro'
    return None
tot = collections.Counter()
for rel, path in C.files(sys.argv[1]):
    xr = C.xbox(rel)
    if xr is None: continue
    X = DW.read(xr, 'be'); P_ = DW.read(open(path, 'rb').read(), 'le')
    xids = {s.id for s in X.sections if s.type == 7}
    pc = collections.defaultdict(list)
    for s in P_.sections:
        if s.type == 7: pc[s.id].append(s)
    for x in X.sections:
        if x.type != 7: continue
        t = table(x, xids)
        if not t: continue
        n, P = t; ps = [p for p in pc.get(im7.get(x.id, x.id), []) if len(p.data) == len(x.data)]
        if len(ps) != 1: print(rel, x.id, 'nessuna coppia PC univoca'); tot['senza coppia'] += 1; continue
        p = ps[0]; d = p.data
        ids = [struct.unpack_from('>I', x.data, P + XS * j + 0x14)[0] for j in range(n)]
        pid = [im7.get(i, i) for i in ids]
        new = b''.join(rec(x.data, P + XS * j, pid[j]) for j in range(n))
        old24 = b''.join(rec(x.data, P + XS * j, pid[j])[:XS] for j in range(n))
        cur = bytes(d[P:P + PS * n])
        if cur == new: k = 'ok passo 0x28'
        elif bytes(d[P:P + XS * n]) == old24: k = 'DIFETTO passo 0x24 (campi giusti)'
        else: k = 'DIFETTO altro'
        tot[k] += 1
        print('%-44s DTP %d n=%d P=+%#x %s%s' % (rel, p.id, n, P, k, '' if k.startswith('ok') else ' | spazio: %s' % (room(x, n, P) or 'si')))
        if not k.startswith('ok'):
            for j in range(n):
                print('      rec %d xbox %s' % (j, x.data[P + XS * j:P + XS * j + XS].hex()))
            print('      pc       %s' % cur.hex())
            print('      atteso   %s' % new.hex())
print('totale', dict(tot))
