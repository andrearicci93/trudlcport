"""fxread_scan.py - (19/11/2026) solo lettura. Regola `fxrecread` del fork di Lukas (logica riscritta): nei record particella
0x17c dei DTP FX (testa +0xc u16 n, +0x10 puntatore T, T + n*0x17c = fine) il lettore tru.exe 0x543f70 legge come u8 i byte di
+0x40 +0x68 +0x7c +0x88 +0x90 +0x11c +0x12c +0x14c +0x174 (-> byte grezzi), +0x58 {u8,u8,u16}, +0x5c u16 al byte 0, +0x160 {u16,u16}.
1) prova sul base: per ogni chiave (offset, parola Xbox) dell'oracolo base work/ws/b268_fxgoo/out/oracle_fx.pkl a quegli offset,
   la forma attesa coincide con la parola PC del base? (conteggi ok / contro)
2) baseline: parole PC diverse dalla forma attesa, per file.
uso: python -I -B fxread_scan.py BASELINE"""
import sys, os, pickle, collections
sys.path.insert(0, '/path/to/trudlcport/work/ws/lukas_check/inv'); sys.path.insert(0, '/path/to/trudlcport/work/ws/b260_cannon'); sys.path.insert(0, '/path/to/trudlcport/tools')
import inv_common as C, drm_write as DW
from fxcal_hdr import fxhdr, ST
P = {'raw': (0, 1, 2, 3), 's16': (1, 0, 3, 2), 'b2s16': (0, 1, 3, 2), 's16b2': (1, 0, 2, 3)}
FX = {0x40: 'raw', 0x68: 'raw', 0x7c: 'raw', 0x88: 'raw', 0x90: 'raw', 0x11c: 'raw', 0x12c: 'raw', 0x14c: 'raw', 0x174: 'raw',
      0x58: 'b2s16', 0x5c: 's16b2', 0x160: 's16'}
def want(x, c): return bytes(x[i] for i in P[c])
OR, OH = pickle.load(open('/path/to/trudlcport/work/ws/b268_fxgoo/out/oracle_fx.pkl', 'rb'))
pr = collections.Counter(); contro = []
for (o, xw), c in OR.items():
    if o not in FX: continue
    w = want(xw, FX[o])
    for pw, n in c.items():
        if pw == w: pr['ok'] += n
        elif pw == xw[::-1] and w == xw[::-1]: pr['ok'] += n
        else: pr['contro'] += n; contro.append((hex(o), xw.hex(), pw.hex(), w.hex(), n))
print('prova base (oracolo):', dict(pr))
for k in sorted(contro, key=lambda t: -t[4])[:15]: print('   contro', *k)
im7 = C.idmap().get(7, {}); tot = collections.Counter()
for rel, path in C.files(sys.argv[1]):
    xr = C.xbox(rel)
    if xr is None: continue
    X = DW.read(xr, 'be'); Pd = DW.read(open(path, 'rb').read(), 'le')
    pc = collections.defaultdict(list)
    for s in Pd.sections:
        if s.type == 7: pc[s.id].append(s)
    for x in X.sections:
        if x.type != 7: continue
        ps = [p for p in pc.get(im7.get(x.id, x.id), []) if len(p.data) == len(x.data)]
        if len(ps) != 1: continue
        p = ps[0]; h = fxhdr(bytes(p.data), bytes(p.reloc), 'le'); hx = fxhdr(bytes(x.data), bytes(x.reloc), 'be')
        if not h or not hx or h[:2] != hx[:2]: continue
        T, n, sl = h; bad = []
        for j in range(n):
            for o, c in sorted(FX.items()):
                a = T + j * ST + o
                if a in sl or a in hx[2]: continue
                xw, pw = bytes(x.data[a:a + 4]), bytes(p.data[a:a + 4]); w = want(xw, c)
                if pw == w: tot['ok'] += 1
                else: tot['diverso'] += 1; bad.append((j, o, xw.hex(), pw.hex(), w.hex()))
        if bad:
            print('%-44s DTP %d n=%d: %d parole diverse' % (rel, p.id, n, len(bad)))
            for j, o, xw, pw, w in bad[:40]: print('    rec %d +%#05x xbox %s pc %s atteso %s' % (j, o, xw, pw, w))
print('totale', dict(tot))
