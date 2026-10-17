"""TASK 1 (giro 3) - prova FUNZIONALE a livello di blocco luci: blocco Xbox Xs (traduzione) vs blocco PC Pd, stessi stati d'ingresso del ponte
(ingressi non-MaterialParams gia' abbinati dal ponte reale), MaterialParams = valori CASUALI (non quelli di un materiale), luci accese.
Per ogni assegnazione candidata dei pareggi: Pd(MP_pc = f(v)) deve coincidere con Xs(MP_xbox = v) su tutte le uscite abbinate, per ogni v."""
import sys, itertools; sys.path.insert(0, '/path/to/trudlcport/work/ws/codefirst')
import numpy as np
from task3_validate import *
import f9m, mp_resolve

def get_ctx(xs, pd):
    L = libs(); X, P = L['X'], L['P']
    xsblob = X[xs]['entries'][X[xs]['slots'][0]]['blob']; pdblob = P[pd]['entries'][P[pd]['slots'][0]]['blob']
    mb = material_pairs(xs, pd); pct = pc_ctab(pdblob); xn = {n: ri for n, rs, ri, rc in pct if rs == 3}
    res, ties = mp_resolve.resolve(xs, pd)
    try: f9m.build(xsblob, pdblob, xsblob, [(m[2], m[3]) for m in mb], x_samp_names=xn, log=[], mp_res=res)
    except Exception as e: print('build:', repr(e)[:150])
    return dict(f9m.CTX), res, ties

def block_run(C, which, consts_rows, N):
    env = C['envx'] if which == 'x' else C['envp']
    consts = dict(env.consts)
    for r, v in consts_rows.items(): consts[r] = np.array(v, np.float32)
    if which == 'x':
        st, prog, a, b, bl = C['sts'], C['sprog'], C['s0'], C['s1'], None
    else:
        st, prog, a, b, bl = C['stp'], C['pprog'], C['p0'], C['p1'], ALLB
    reg, kill = run_state(prog, body(prog)[a:b], st, consts, env.tex, env.N, bl)
    return reg

def outs_agree(C, regx, regp):
    ok = []
    for po, so in C['p_to_s_out'].items():
        a = regp.get((0, po[0])); b = regx.get((0, so[0]))
        if a is None or b is None: ok.append(0.0); continue
        ok.append(float(np.isclose(a[:, po[1]], b[:, so[1]], **TOL).mean()))
    return ok

def pc_rows(C, res, assign, v):
    """righe c100.. del PC dal vettore Xbox v ({(r,c): val}) con la regola res; assign = {lane_pc: lane_xbox} per i pareggi."""
    rows = {}
    for (r, c), (kind, val) in res.items():
        if kind == 'const': x = val
        elif kind == 'lane': x = v[tuple(val)]
        elif kind == 'tie': x = v[tuple(assign[(r, c)])]
        else: raise ValueError(kind)
        rows.setdefault(r, [0.0] * 4)[c] = float(x)
    return rows

def main(xs, pd, K=6):
    C, res, ties = get_ctx(xs, pd)
    rng = np.random.RandomState(77)
    ms = sorted(C['ms'])
    XPb = C['XP']
    draws = []
    for _ in range(K):
        v = {l: float(rng.uniform(0.05, 2.0)) for l in ms}
        draws.append(v)
    # base: ponte reale (valori del materiale) -> verifica che le uscite coincidano a luci accese
    # per ogni assegnazione
    tl = sorted(ties)
    combos = list(itertools.product(*[ties[l] for l in tl]))
    print('=== (%d,%d) lane Xs lette %d, pareggi %s, combinazioni %d' % (xs, pd, len(ms), ['c%d.%s' % (l[0], 'xyzw'[l[1]]) for l in tl], len(combos)))
    table = []
    for cb in combos:
        assign = dict(zip(tl, cb)); sc = []
        for v in draws:
            rows_x = {}
            for (r, c), val in v.items(): rows_x.setdefault(r, [0.0] * 4)[c] = val
            rx = block_run(C, 'x', rows_x, C['envx'].N)
            rp = block_run(C, 'p', pc_rows(C, res, assign, v), C['envp'].N)
            sc.append(outs_agree(C, rx, rp))
        sc = np.array(sc)
        table.append((float(sc.mean()), float(sc.min()), assign))
    table.sort(key=lambda t: -t[0])
    for m, mn, a in table[:12]:
        print('  media %.4f min %.4f  %s' % (m, mn, {('c%d.%s' % (l[0], 'xyzw'[l[1]])): ('c%d.%s' % (x[0], 'xyzw'[x[1]])) for l, x in a.items()}))
    print('  ... peggiore %.4f' % table[-1][0], ' n con media>=0.999:', sum(1 for t in table if t[0] >= 0.999))
if __name__ == '__main__': main(int(sys.argv[1]), int(sys.argv[2]))
