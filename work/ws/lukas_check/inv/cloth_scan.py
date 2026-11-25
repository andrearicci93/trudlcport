"""cloth_scan.py - (19/11/2026) solo lettura. Verifica del passo `cloth` del fork (suo dlc_fixes_build.fix_cloth,
logica riscritta): blocchi parametri cloth dei DTP (tipo 7, id PC >= 20000) {.., ptr(-20), .., ptr(-12), .., .., u32 iter,
u32, u32, u32}: sul sorgente Xbox puntatori a -20 e -12, nessuna rilocazione a -8..+12, interi 1..0xff a +0/+4/+8/+12.
Difetto = parola PC == scambio s16 della parola Xbox (es. 4 -> 00000400 LE = 0x00040000 = 262144) e != s32.
Riporta anche la classe di ogni conteggio (s32 ok / s16 difetto / altro).
uso: python -I -B cloth_scan.py BASELINE"""
import sys, os, struct, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, '/path/to/trudlcport/tools')
import inv_common as C, drm_write as DW, drm_reloc as R
BL = sys.argv[1]
L = C.Log(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cloth_scan_%s.log' % BL.split('_')[0]))
im7 = C.idmap().get(7, {})


def pairs(X, P):
    if len(X) == len(P) and all(x.type == p.type for x, p in zip(X, P)): return list(zip(X, P)), 'indice'
    pi = {}
    for p in P:
        if p.type == 7: pi.setdefault(p.id, []).append(p)
    out = []
    for x in X:
        if x.type != 7: continue
        c = pi.get(im7.get(x.id, x.id), [])
        if len(c) == 1: out.append((x, c[0]))
    return out, 'id'


tot = collections.Counter()
for rel, path in C.files(BL):
    xr = C.xbox(rel)
    if xr is None: tot['senza xbox'] += 1; continue
    X = DW.read(xr, 'be').sections; P = DW.read(open(path, 'rb').read(), 'le').sections
    tot['file'] += 1
    prs, how = pairs(X, P)
    for x, p in prs:
        if x.type != 7 or p.type != 7 or p.id < 20000 or len(x.data) != len(p.data) or not x.data: continue
        xd, pd = x.data, p.data
        xrr = R.parse(x.reloc, 'be'); ptr = set(xrr.pointer_offsets()); sl = ptr | set(xrr.id_offsets())
        for o in range(20, len(xd) - 15, 4):
            if o - 20 not in ptr or o - 12 not in ptr or any(k in sl for k in (o - 8, o - 4, o, o + 4, o + 8, o + 12)): continue
            v = [struct.unpack_from('>I', xd, o + d)[0] for d in (0, 4, 8, 12)]
            if not all(0 < w < 0x100 for w in v): continue
            xw = xd[o:o + 4]; pw = pd[o:o + 4]; want = struct.pack('<I', v[0])
            k = 's32 ok' if pw == want else ('s16 DIFETTO' if pw == xw[1::-1] + xw[:1:-1] else 'altro')
            tot['blocchi ' + k] += 1
            if k != 's32 ok': L('%s %s DTP %d +0x%x xbox %s pc %s (iter %d -> PC legge %d)' % (k, rel, p.id, o, xw.hex(), pw.hex(), v[0], struct.unpack('<I', pw)[0]))
L('TOTALE %s' % dict(sorted(tot.items())))
