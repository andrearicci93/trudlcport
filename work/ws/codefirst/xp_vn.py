"""TASK 1 (giro 3): isomorfismo di dataflow per VALUE NUMBERING. Si eseguono il blocco luci Xbox (Xs, traduzione) e il blocco PC (Pd) con una VM che
registra il vettore di valori di OGNI istruzione (nodo del DAG), con MaterialParams casuali condivisi secondo l'ipotesi H (lane PC = lane Xbox).
Un nodo PC e' ALLINEATO se un nodo Xbox ha lo stesso vettore su tutti i pixel (non costante). L'ipotesi giusta allinea le sotto-espressioni che
dipendono dalla lane; le sbagliate le rompono. Nessun valore di materiale reale, nessun campione unico."""
import sys, itertools, collections; sys.path.insert(0, '/path/to/trudlcport/work/ws/codefirst')
import numpy as np
from xp_func import *
import sm3vm

class TraceVM(sm3vm.VM):
    def __init__(self, *a, **k):
        super().__init__(*a, **k); self.tr = []; self._cur = None
    def _alu(self, it, s):
        self._cur = it; return super()._alu(it, s)
    def write(self, o, val, mask):
        super().write(o, val, mask)
        if self._cur is not None:
            v = self.reg[(o.rtype, o.num)]
            self.tr.append((self._cur, [v[:, c].copy() if (o.wm >> c & 1) else None for c in range(4)]))
            self._cur = None

def trace(C, which, rows, bools):
    env = C['envx'] if which == 'x' else C['envp']; consts = dict(env.consts)
    for r, v in rows.items(): consts[r] = np.array(v, np.float32)
    if which == 'x': st, prog, a, b = C['sts'], C['sprog'], C['s0'], C['s1']
    else: st, prog, a, b = C['stp'], C['pprog'], C['p0'], C['p1']
    vm = TraceVM(sub_program(prog, body(prog)[a:b]), env.N, {k: v.copy() for k, v in st.items()}, consts, env.tex, bools)
    vm.exec()
    return prog, vm.tr

def key(v):
    return tuple(np.round(v[:6].astype(np.float64), 3))

def nodes(prog, tr):
    out = []
    for n, (it, vals) in enumerate(tr):
        for c, v in enumerate(vals):
            if v is None or not np.all(np.isfinite(v)) or np.std(v) < 1e-5: continue
            out.append((n, c, it, v))
    return out

def align(nx, np_):
    idx = collections.defaultdict(list)
    for n, c, it, v in nx: idx[key(v)].append((n, c, it, v))
    hits = {}
    for n, c, it, v in np_:
        for m, cx, itx, vx in idx.get(key(v), []):
            if np.allclose(v, vx, rtol=2e-3, atol=2e-4): hits[(n, c)] = (m, cx); break
    return hits

def score(C, res, assign, draws):
    tot = 0; per = []
    for v in draws:
        rows_x = {}
        for (r, c), val in v.items(): rows_x.setdefault(r, [0.0] * 4)[c] = val
        px, tx = trace(C, 'x', rows_x, None); pp, tp = trace(C, 'p', pc_rows(C, res, assign, v), ALLB)
        nx, npc = nodes(px, tx), nodes(pp, tp)
        h = align(nx, npc); tot += len(h); per.append((len(h), len(npc)))
    return tot, per

def main(xs, pd, K=2):
    C, res, ties = get_ctx(xs, pd)
    rng = np.random.RandomState(31); ms = sorted(C['ms'])
    draws = [{l: float(rng.uniform(0.2, 2.0)) for l in ms} for _ in range(K)]
    tl = sorted(ties); combos = list(itertools.product(*[ties[l] for l in tl]))
    print('=== (%d,%d) pareggi %s: %d combinazioni; K=%d' % (xs, pd, ['c%d.%s' % (l[0], 'xyzw'[l[1]]) for l in tl], len(combos), K), flush=True)
    rows = []
    for cb in combos:
        assign = dict(zip(tl, cb)); t, per = score(C, res, assign, draws)
        rows.append((t, per, assign))
    rows.sort(key=lambda r: -r[0])
    for t, per, a in rows[:15]:
        print('  allineati %5d %s  %s' % (t, per, {('c%d.%s' % (l[0], 'xyzw'[l[1]])): ('c%d.%s' % (x[0], 'xyzw'[x[1]])) for l, x in a.items()}), flush=True)
    print('  ... ultimo', rows[-1][0])
    import pickle; pickle.dump((rows, tl), open('xp_vn_%d_%d.pkl' % (xs, pd), 'wb'))
if __name__ == '__main__': main(int(sys.argv[1]), int(sys.argv[2]))
