"""chain_diff.py - verifica la catena (md5 di ogni anello), salva i delta per stadio (deltas/NN_stadio.json) e scrive PATCHES.tsv
(differenze byte 56d1ce2d -> 2b7ee74c per intervallo contiguo, stadio responsabile = ultimo stadio che ha scritto quei byte).
uso: python -I -B chain_diff.py"""
import sys, os, json, hashlib, numpy as np, pefile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chain import CHAIN, W
OUT = 'C:/tru-port/work/ws/exe_chain/'


def secmap(path):
    pe = pefile.PE(path, fast_load=True)
    r = [(s.Name.rstrip(b'\0').decode(), s.PointerToRawData, s.SizeOfRawData, 0x400000 + s.VirtualAddress, s.Misc_VirtualSize) for s in pe.sections]
    pe.close(); return r


def where(secs, off):
    for nm, rp, rs, va, vs in secs:
        if rp <= off < rp + rs: return nm, va + off - rp
    return 'HDR', (0x400000 + off if off < 0x1000 else None)


nodes = [c for c in CHAIN if c[2]]
final = open(W + nodes[-1][2], 'rb').read(); L = len(final)
FS = secmap(W + nodes[-1][2])
last = np.full(L, -1, np.int16)
prev = None; rows = []
for i, (nm, m, p, sc, ex) in enumerate(nodes):
    b = open(W + p, 'rb').read(); md = hashlib.md5(b).hexdigest()
    assert md.startswith(m), (nm, md, m)
    A = np.frombuffer(b + bytes(L - len(b)), np.uint8)
    if prev is not None:
        idx = np.nonzero(A != prev[1])[0]
        last[idx] = i
        rs = []; s = e = None
        for k in idx.tolist():
            if s is not None and k == e + 1: e = k; continue
            if s is not None: rs.append((s, e))
            s = e = k
        if s is not None: rs.append((s, e))
        delta = dict(stage=nm, input_md5=prev[2], output_md5=md, output_size=len(b), ranges=[[a, A[a:z + 1].tobytes().hex()] for a, z in rs])
        json.dump(delta, open(OUT + 'deltas/%02d_%s.json' % (i, nm), 'w'))
        rows.append((nm, prev[2], md, len(idx), len(rs), len(b) - prev[3]))
    prev = (nm, A, md, len(b))
print('stadio\tin\tout\tbyte\tintervalli\tdelta_size')
for r in rows: print('%s\t%s\t%s\t%d\t%d\t%+d' % r)
vb = open(W + nodes[0][2], 'rb').read()
V = np.frombuffer(vb + bytes(L - len(vb)), np.uint8)
F = np.frombuffer(final, np.uint8)
vanilla_secs = {s[0] for s in secmap(W + nodes[0][2])}
newsec = {s[0] for s in FS if s[0] not in vanilla_secs}
idx = np.nonzero(F != V)[0]
names = [n[0] for n in nodes]
out = open(OUT + 'PATCHES.tsv', 'w', newline='\n')
out.write('va\tfile_off\tlen\tsezione\tbyte_orig(<=32B)\tbyte_nuovi(<=32B)\tstadio\n')


def emit(a, z):
    nm, va = where(FS, a)
    st = sorted({names[x] for x in last[a:z + 1].tolist() if x >= 0}, key=names.index)
    out.write('%s\t0x%x\t%d\t%s\t%s\t%s\t%s\n' % (hex(va) if va is not None else '-', a, z - a + 1, nm,
              V[a:z + 1][:32].tobytes().hex(), F[a:z + 1][:32].tobytes().hex(), '+'.join(st)))


s = e = None; n = 0
for k in idx.tolist():
    if where(FS, k)[0] in newsec: continue
    if s is not None and k == e + 1: e = k; continue
    if s is not None: emit(s, e); n += 1
    s = e = k
if s is not None: emit(s, e); n += 1
for nm, rp, rs, va, vs in FS:
    if nm in newsec:
        st = sorted({names[x] for x in last[rp:rp + rs].tolist() if x >= 0}, key=names.index)
        blob = final[rp:rp + rs]
        out.write('%s\t0x%x\t%d\t%s\t(sezione nuova: vsize 0x%x raw 0x%x md5 %s, %d byte non nulli)\t-\t%s\n' % (
            hex(va), rp, rs, nm, vs, rs, hashlib.md5(blob).hexdigest(), int(np.count_nonzero(np.frombuffer(blob, np.uint8))), '+'.join(st)))
out.close()
print('PATCHES.tsv: %d intervalli nelle sezioni originali/header + %d sezioni nuove; byte diversi totali %d' % (n, len(newsec), len(idx)))
