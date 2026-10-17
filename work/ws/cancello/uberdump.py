"""Dump dei dati UberObject di un oggetto (DTP dati oggetto, blocco a +0xc0): parti, grafo (nodi, azioni, transizioni),
liste comandi, trigger. Xbox grezzo e B83 affiancati. Uso: uberdump.py <oggetto.drm> <id DTP>"""
import sys, os, struct
H = os.path.dirname(os.path.abspath(__file__)); T = os.path.join(H, '..', '..', '..', 'tools'); sys.path.insert(0, T)
import drm, drm_reloc as R
from wave_swap import raw_dlc
name, sid = sys.argv[1], int(sys.argv[2])
def load(side):
    raw, e = (open(os.path.join(T, '..', 'work', 'baseline', 'B83', 'mods', name), 'rb').read(), 'le') if side == 'pc' else (raw_dlc(name)[0], 'be')
    secs = drm.sections_with_data(drm.cdrm_decode(raw, e), e)[1]
    s = [x for x in secs if x['type'] == 7 and x['id'] == sid][0]
    return s['data'], dict(R.parse(s['reloc'], e).internal), ('<' if e == 'le' else '>')
class V:
    def __init__(s, side): s.d, s.it, s.E = load(side)
    def u(s, o): return struct.unpack_from(s.E + 'I', s.d, o)[0]
    def h(s, o): return struct.unpack_from(s.E + 'HH', s.d, o)
    def f(s, o): return round(struct.unpack_from(s.E + 'f', s.d, o)[0], 3)
    def p(s, o): return s.it.get(o)
    def name(s, o):
        t = s.p(o)
        if t is None: return None
        e = s.d.find(b'\0', t); return s.d[t:e].decode('latin1', 'replace')
def dump(v, out):
    blk = v.p(0xc0); out.append('blocco @%s' % blk)
    if blk is None: return
    np_, pp = v.u(blk + 8), v.p(blk + 0xc); nl, lp = v.u(blk + 0x10), v.p(blk + 0x14); nt, tp = v.u(blk + 0x18), v.p(blk + 0x1c)
    out.append('parti %d liste %d trigger %d  (+0x28 %d +0x30 %d)' % (np_, nl, nt, v.u(blk + 0x28), v.u(blk + 0x30)))
    for k in range(nl):
        a = lp + 12 * k; n = v.u(a + 4); c = v.p(a + 8)
        out.append('  lista %d: %s' % (k, [tuple(v.u(c + 12 * j + q) for q in (0, 4, 8)) for j in range(n)] if c is not None else []))
    for k in range(nt):
        a = tp + 0x1c * k
        out.append('  trigger %d: n_cond %d kind %d nodo %d param %d once %d fx %s' % (k, v.u(a + 4), v.u(a + 0x10), v.u(a + 0xc), v.u(a + 0x14), v.d[a + 0x18], v.h(a + 0x18)))
    for k in range(np_):
        a = pp + 0x54 * k
        out.append(' parte %d @%d: modello %d flags+0x2c %08x +0x18..: %s  float+0x28 %s  +0x50 %08x' % (k, a, v.d[a + 0x18], v.u(a + 0x2c), v.d[a + 0x18:a + 0x20].hex(), v.f(a + 0x28), v.u(a + 0x50)))
        nn, nd = v.u(a + 4), v.p(a + 8); ntr, trp = v.u(a + 0xc), v.p(a + 0x10)
        out.append('   nodi %d transizioni %d iniziale %d' % (nn, ntr, v.u(a + 0x14)))
        tb = {}
        for j in range(ntr):
            t = trp + 0x38 * j; tb[t] = j
            out.append('   T%d -> nodo %d cond 0x%x arg %08x(%s) n%d anim %s prob %d +0x30 %08x flags %02x' % (j, v.u(t + 4), v.u(t + 0x18), v.u(t + 0x1c), v.f(t + 0x1c), v.u(t + 8), v.h(t + 0x28), v.u(t + 0x2c), v.u(t + 0x30), v.d[t + 0x34]))
        for j in range(nn):
            o = nd + 0x1c * j; nt_, tq = v.u(o + 0xc), v.p(o + 0x10); na, ap = v.u(o + 0x14), v.p(o + 0x18)
            tl = [tb.get(v.p(tq + 4 * q)) for q in range(nt_)] if tq is not None else []
            acts = [(v.u(ap + 16 * q), v.d[ap + 16 * q + 4:ap + 16 * q + 16].hex()) for q in range(na)] if ap is not None else []
            out.append('   N%d %s trans %s azioni %s' % (j, v.name(o + 8), tl, acts))
a, b = [], []
dump(V('xb'), a); dump(V('pc'), b)
for x, y in zip(a, b):
    print(('   ' if x == y else '!! ') + y + ('' if x == y else '\n   XB ' + x))
