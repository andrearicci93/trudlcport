"""Lista comandi dei DTP cine (es. 22643): record {u16 tipo, u16 fotogramma, ...}. Impara la lunghezza per byte alto del tipo
dalle coppie base (parse sequenziale che deve coprire tutto il DTP) e la classe per (tipo, indice parola)."""
import sys, os, struct, collections, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dtp_rules as DR      # riusa le coppie gia' raccolte (pairs, cls)
pairs, cls = DR.pairs, DR.cls
def walk(d, size):
    o, recs = 0, []
    while o + 4 <= len(d):
        hb = d[o]
        if hb not in size: return None, o
        n = size[hb]; recs.append((o, d[o:o + 2].hex(), n)); o += n
    return recs, o
# byte alti visti all'inizio dei DTP-comando
starts = collections.Counter(x['data'][0] for _, x, _ in pairs)
print('byte iniziali', {hex(k): v for k, v in starts.items()})
SIZES = (8, 12, 16, 20, 24, 28, 32)
def solve(d, size, o=0, depth=0):
    """DFS: estende la tabella size finche' il parse copre esattamente d (o termina in una coda testo/zero)"""
    if o == len(d): return size
    if o + 4 > len(d): return None
    hb = d[o]
    if hb == 0 or hb == 0xff: return None
    cands = [size[hb]] if hb in size else SIZES
    for n in cands:
        s2 = dict(size); s2[hb] = n
        r = solve(d, s2, o + n, depth + 1)
        if r is not None: return r
    return None
import sys as _s; _s.setrecursionlimit(100000)
size = {}
order = sorted(pairs, key=lambda t: len(t[1]['data']))
ok = bad = 0; fails = []
for n, x, p in order:
    d = x['data']; off = 4 if d[0] == 0 else 0
    r = solve(d[off:], size)
    if r is None: bad += 1; fails.append((n, x['id'], len(d), d[off:off + 8].hex()))
    else: size = r; ok += 1
print('parse ok', ok, 'falliti', bad, 'tabella', {hex(k): v for k, v in sorted(size.items())})
for f in fails[:12]: print('  fallito', f)
