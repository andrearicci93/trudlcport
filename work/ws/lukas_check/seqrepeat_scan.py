"""seqrepeat_scan.py - (19/11/2026) solo lettura, dalla segnalazione di Lukas (issue #5, suo finding 49):
nodi SoundPlex Sequence (tipo 10), data = {+0 u32 count, +4 ptr figli, +8 ptr, +0xc s8 repeat + 3 byte}.
Xbox legge il PRIMO byte della parola +0xc (lbz), il PC movsx byte [data+0xc]: la parola va copiata grezza.
Lo scambio a 32 bit da' repeat 0 = ripeti per sempre. Confronto per posizione col DRM Xbox (pack11/pack10).
uso: python -I -B seqrepeat_scan.py BASELINE [--all]"""
import sys, os, struct, collections
sys.path.insert(0, '/path/to/trudlcport/tools')
import drm_write as DW, drm_reloc as R
from archive import Archive
from dlc_names import PACKS, fcrc
B = '/path/to/trudlcport/work/baseline/%s/mods/' % sys.argv[1]; ALL = '--all' in sys.argv
A = [Archive(PACKS[p], 'be') for p in ('pack11', 'pack10')]
BS = chr(92)
def xbox(rel):
    h = fcrc('xenon-w' + BS + rel.replace('/', BS))
    for a in A:
        rs = [r for r in a.idx if r['hash'] == h]
        if rs: return a.read(rs[0])
def seq_nodes(xd, xr):
    rel = R.parse(xr, 'be'); it = dict(rel.internal); slots = set(rel.pointer_offsets()) | set(rel.id_offsets())
    out = []
    for o, tg in rel.internal:
        if o < 4 or o % 4 or (o - 4) in slots: continue
        if struct.unpack_from('>I', xd, o - 4)[0] != 10 or tg % 4 or tg + 0x10 > len(xd): continue
        if tg in slots or tg + 0xc in slots: continue
        cnt = struct.unpack_from('>I', xd, tg)[0]; arr = it.get(tg + 4)
        if not 1 <= cnt <= 256 or arr is None or arr + 4 * cnt > len(xd): continue
        ok = all((ch := it.get(arr + 4 * j)) is not None and ch + 8 <= len(xd) and struct.unpack_from('>I', xd, ch)[0] <= 13 and ch + 4 in it for j in range(cnt))
        if ok: out.append(tg)
    return sorted(set(out))
cls = collections.Counter(); bad = []; files = 0
for root, _, fs in os.walk(B):
    for f in sorted(fs):
        if not f.endswith('.drm'): continue
        rel = os.path.relpath(os.path.join(root, f), B).replace(BS, '/')
        xr = xbox(rel)
        if xr is None: continue
        try: X = DW.read(xr, 'be').sections; P = DW.read(open(os.path.join(root, f), 'rb').read(), 'le').sections
        except Exception as e: print('ERR', rel, e); continue
        files += 1
        if len(X) == len(P): prs = list(zip(X, P))
        else:   # numero di sezioni diverso: coppia per forma (tipo 7, stessa dimensione, stessi puntatori interni), unica
            prs = []
            for x in X:
                if x.type != 7 or not x.reloc or not seq_nodes(x.data, x.reloc): continue
                xi = dict(R.parse(x.reloc, 'be').internal)
                c = [p for p in P if p.type == 7 and len(p.data) == len(x.data) and p.reloc and dict(R.parse(p.reloc, 'le').internal) == xi]
                if len(c) == 1: prs.append((x, c[0]))
                elif c:   # ambigua: conta tutti i candidati, li segna se non sono tutti grezzi
                    ks = {c_.id: all(x.data[t + 0xc:t + 0x10] == c_.data[t + 0xc:t + 0x10] for t in seq_nodes(x.data, x.reloc)) for c_ in c}
                    if all(ks.values()): prs.append((x, c[0]))
                    else: print('AMBIGUA', rel, x.id, ks)
                else: print('NOPAIR', rel, x.id)
        for x, p in prs:
            if x.type != 7 or len(x.data) != len(p.data) or not x.reloc: continue
            for tg in seq_nodes(x.data, x.reloc):
                xw, pw = x.data[tg + 0xc:tg + 0x10], p.data[tg + 0xc:tg + 0x10]
                k = 'raw' if xw == pw else ('u32' if xw[::-1] == pw else 'altro')
                cls[k] += 1
                if k != 'raw' or ALL:
                    line = '%s %s DTP %d->%d +0x%x xbox %s pc %s repeat xbox %d pc %d' % (k, rel, x.id, p.id, tg, xw.hex(), pw.hex(), struct.unpack('b', xw[:1])[0], struct.unpack('b', pw[:1])[0])
                    print(line)
                    if k != 'raw': bad.append(line)
print('file %d, nodi Sequence %s, da correggere %d' % (files, dict(cls), len(bad)))
