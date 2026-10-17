"""F6 - equivalenza NUMERICA shader DLC illuminato vs gemello Xbox del surrogato (Xbox vs Xbox, stesso compilatore).
Costanti associate per NOME (stesso registro finto per stesso (nome, indice)), sampler per registro, bool per nome.
Se non equivalenti: cerca una permutazione delle componenti MaterialParams (impronta = variazione dell'uscita perturbando
una sola componente) e riprova con la mappa trovata.
uso: tools/venv/bin/python -I work/ws/shader4/f6_equiv_lit.py [id_dlc ...]   (default: lib dei materiali difettosi + tutte le 54)
uscita: work/ws/shader4/f6_equiv_lit.tsv + riassunto a schermo"""
import sys, os, csv, itertools, collections
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from f3_validate import *
import xenos_xlat as XL
from f5_census_lit import bool_names, ps_slots, ctab_sig

N = 400


class Names:
    def __init__(self): self.reg = {}
    def fn(self, name, j, count):
        k = (name, j)
        if k not in self.reg: self.reg[k] = len(self.reg)
        return self.reg[k] if self.reg[k] < 200 else None


def translate(blob, names, bv):
    sh = XL.parse(blob); bn = bool_names(sh)
    bools = {i: bv.get(n, 0) for i, n in bn.items()}
    t = xenos2sm3.translate(blob, names.fn, bools=bools, samp=lambda n, c: c)
    return sm3asm.parse_text(t.text)


def run(prog, consts, seed=3):
    rng = np.random.RandomState(seed)
    ins, vmap = inputs_of(prog)
    vals = {}
    for s in sorted(set(ins) | {(u, i) for u in range(16) for i in range(16)}, key=str):
        vals[s] = rng.uniform(0, 1, (N, 4)).astype(np.float32)   # stesso ingresso per stessa semantica in A e B
    d = {(sm3asm.RT_INPUT, vmap[s]): vals[s] for s in vmap if s[0] != 'misc'}
    d[(sm3asm.RT_MISC, 0)] = np.tile(np.float32([700, 300, 0, 0]), (N, 1)) + rng.uniform(0, 1, (N, 4)).astype(np.float32)
    d[(sm3asm.RT_MISC, 1)] = np.ones((N, 4), np.float32)
    o = sm3vm.run(prog, d, consts, sm3vm.det_tex(lambda s: s), N)
    return np.where(o['kill'][:, None], np.nan, o.get('oC0', np.zeros((N, 4), np.float32)))


def close(a, b):
    m = ~(np.isnan(a) | np.isnan(b))
    if (np.isnan(a) != np.isnan(b)).mean() > 0.01: return 0.0
    ok = np.abs(a - b) <= 1e-3 * np.maximum(np.abs(a), np.abs(b)) + 2e-4
    return float((ok | ~m).all(axis=1).mean())


def base_consts(names, seed=11):
    rng = np.random.RandomState(seed)
    return {r: rng.uniform(0.05, 1.5, 4).astype(np.float32) for r in range(224)}


def mp_regs(names):
    return {j: r for (n, j), r in names.reg.items() if n == 'MaterialParams'}


def fingerprints(prog, names, C):
    """{(j, comp): delta uscita} perturbando una componente di MaterialParams[j]."""
    y0 = run(prog, C); fp = {}
    for j, r in mp_regs(names).items():
        for c in range(4):
            C2 = dict(C); v = C[r].copy(); v[c] += 0.37; C2[r] = v
            d = run(prog, C2) - y0
            if np.nanmax(np.abs(d)) > 1e-5: fp[(j, c)] = d
    return fp


def match_mp(pa, pb, names, C):
    fa, fb = fingerprints(pa, names, C), fingerprints(pb, names, C)
    mp = {}
    for ka, da in fa.items():
        best = [kb for kb, db in fb.items() if close(da, db) > 0.98]
        if len(best) == 1: mp[ka] = best[0]
    return mp, len(fa), len(fb)


def compare_pair(dl, xt):
    L = libs(); D, X = L['D'], L['X']
    out = []
    for s in ps_slots(D[dl]):
        if s >= len(X[xt]['slots']) or X[xt]['slots'][s] == 0xffffffff: continue
        bd = D[dl]['entries'][D[dl]['slots'][s]]['blob']; bx = X[xt]['entries'][X[xt]['slots'][s]]['blob']
        bnames = sorted(set(bool_names(XL.parse(bd)).values()))
        for combo in itertools.product((0, 1), repeat=min(len(bnames), 4)):
            bv = dict(zip(bnames, combo)); names = Names()
            try:
                pa = translate(bd, names, bv); pb = translate(bx, names, bv)
            except xenos2sm3.Reject as e:
                continue
            C = base_consts(names)
            f = close(run(pa, C), run(pb, C))
            res = dict(slot=s, bools=bv, frac=f)
            if f < 0.99:
                mp, na, nb = match_mp(pa, pb, names, C)
                res.update(mp_used_dlc=na, mp_used_base=nb, mp_matched=len(mp),
                           mp_moved=sorted('%d%s->%d%s' % (a[0], 'xyzw'[a[1]], b[0], 'xyzw'[b[1]]) for a, b in mp.items() if a != b))
                # riprova: valori DLC spostati nelle posizioni lette dal gemello
                if mp and len(mp) == na:
                    regs = mp_regs(names); C2 = dict(C)
                    for (ja, ca), (jb, cb) in mp.items():
                        v = C2[regs[jb]].copy(); v[cb] = C[regs[ja]][ca]; C2[regs[jb]] = v
                    res['frac_dopo_mappa'] = close(run(pa, C), run(pb, C2))
            out.append(res)
    return out


def main():
    L = libs(); X = L['X']
    rev = collections.defaultdict(list)
    for x, p in x2p().items(): rev[p].append(x)
    rows = {int(r['id_xbox']): r for r in csv.DictReader(open(os.path.join(HERE, 'illuminati.tsv')), delimiter='\t')}
    ids = [int(a) for a in sys.argv[1:]] or [2170, 2191, 2244, 2247, 2121, 2264] + sorted(set(rows) - {2170, 2191, 2244, 2247, 2121, 2264})
    lines = ['id_dlc\tgemello\tslot\tbools\tfrac\tmp_dlc\tmp_base\tmp_match\tspostati\tfrac_dopo_mappa']
    summ = collections.Counter()
    for dl in ids:
        pc = int(rows[dl]['id_pc_surrogato'])
        tw = [x for x in rev.get(pc, []) if X[x]['kind'] == 1]
        if not tw: summ['nogemello'] += 1; continue
        sd = ctab_sig(XL.parse(L['D'][dl]['entries'][L['D'][dl]['slots'][0]]['blob']))
        xt = max(tw, key=lambda x: sum(1 for k in sd[1] if k in ctab_sig(XL.parse(X[x]['entries'][X[x]['slots'][0]]['blob']))[1]))
        res = compare_pair(dl, xt)
        if not res: summ['nessuna_permutazione_traducibile'] += 1; print(dl, 'nessuna permutazione traducibile'); continue
        best = max(r.get('frac_dopo_mappa', r['frac']) for r in res)
        eq = min(r['frac'] for r in res)
        verdict = 'EQUIVALENTE' if eq >= 0.99 else ('EQUIV_CON_MAPPA_MP' if all(r.get('frac_dopo_mappa', r['frac']) >= 0.99 for r in res) else 'DIVERSO')
        summ[verdict] += 1
        r0 = [r for r in res if r['frac'] < 0.99][:1] or res[:1]
        print(dl, 'gemello', xt, verdict, 'perm', len(res), 'frac min %.3f' % eq, 'max dopo mappa %.3f' % best,
              'esempio:', {k: v for k, v in r0[0].items() if k != 'bools'})
        for r in res:
            lines.append('\t'.join(str(x) for x in (dl, xt, r['slot'], r['bools'], '%.3f' % r['frac'], r.get('mp_used_dlc', ''), r.get('mp_used_base', ''),
                                                    r.get('mp_matched', ''), ','.join(r.get('mp_moved', [])), r.get('frac_dopo_mappa', ''))))
    open(os.path.join(HERE, 'f6_equiv_lit.tsv'), 'w').write('\n'.join(lines) + '\n')
    print(dict(summ))


if __name__ == '__main__':
    main()
