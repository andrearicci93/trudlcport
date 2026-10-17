"""F6b - le DIVERSO di f6 sono solo texture scambiate di slot? Test rapido equivalente alla prova di tutte le permutazioni: TUTTI i sampler
restituiscono la stessa texture (funzione indipendente dal sampler). Se due shader differiscono solo per lo slot delle texture, qui coincidono.
Se coincidono qui ma non in f6 -> texture scambiate (correggibile riassegnando gli slot); se differiscono anche qui -> codice diverso davvero.
Per prudenza si ripete anche con la ricerca della mappa MaterialParams di f6.
uso: tools/venv/bin/python -I work/ws/shader4/f6b_sampler_perm.py [id_dlc ...]   (default: tutte le 54; prima le 6 dei materiali difettosi)
uscita: work/ws/shader4/f6b_sampler_perm.txt"""
import sys, os, itertools, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import f6_equiv_lit as F6
from f6_equiv_lit import *

DEF = [2170, 2191, 2244, 2247, 2121, 2264]


def run_same_tex(prog, consts, seed=3):
    """come f6.run ma con la stessa texture per ogni sampler"""
    rng = np.random.RandomState(seed)
    ins, vmap = inputs_of(prog)
    vals = {s: rng.uniform(0, 1, (N, 4)).astype(np.float32) for s in sorted(set(ins) | {(u, i) for u in range(16) for i in range(16)}, key=str)}
    d = {(sm3asm.RT_INPUT, vmap[s]): vals[s] for s in vmap if s[0] != 'misc'}
    d[(sm3asm.RT_MISC, 0)] = np.tile(np.float32([700, 300, 0, 0]), (N, 1)) + rng.uniform(0, 1, (N, 4)).astype(np.float32)
    d[(sm3asm.RT_MISC, 1)] = np.ones((N, 4), np.float32)
    o = sm3vm.run(prog, d, consts, sm3vm.det_tex(lambda s: 0), N)
    return np.where(o['kill'][:, None], np.nan, o.get('oC0', np.zeros((N, 4), np.float32)))


def main():
    L = libs(); D, X = L['D'], L['X']
    rev = collections.defaultdict(list)
    for x, p in x2p().items(): rev[p].append(x)
    rows = {int(r['id_xbox']): r for r in csv.DictReader(open(os.path.join(HERE, 'illuminati.tsv')), delimiter='\t')}
    ids = [int(a) for a in sys.argv[1:]] or DEF + sorted(set(rows) - set(DEF))
    F6.run = run_same_tex            # anche match_mp usa la texture unica
    out = []; cnt = collections.Counter()
    for dl in ids:
        pc = int(rows[dl]['id_pc_surrogato'])
        tw = [x for x in rev.get(pc, []) if X[x]['kind'] == 1]
        if not tw: continue
        best = None
        for xt in tw:
            for s in ps_slots(D[dl]):
                if s >= len(X[xt]['slots']) or X[xt]['slots'][s] == 0xffffffff: continue
                bd = D[dl]['entries'][D[dl]['slots'][s]]['blob']; bx = X[xt]['entries'][X[xt]['slots'][s]]['blob']
                bnames = sorted(set(bool_names(XL.parse(bd)).values()))
                for combo in itertools.product((0, 1), repeat=min(len(bnames), 4)):
                    bv = dict(zip(bnames, combo)); names = Names()
                    try: pa = translate(bd, names, bv); pb = translate(bx, names, bv)
                    except xenos2sm3.Reject: continue
                    C = base_consts(names); f = close(run_same_tex(pa, C), run_same_tex(pb, C)); fm = f
                    if f < 0.99:
                        mp, na, nb = match_mp(pa, pb, names, C)
                        if mp and len(mp) == na:
                            regs = mp_regs(names); C2 = dict(C)
                            for (ja, ca), (jb, cb) in mp.items():
                                v = C2[regs[jb]].copy(); v[cb] = C[regs[ja]][ca]; C2[regs[jb]] = v
                            fm = close(run_same_tex(pa, C), run_same_tex(pb, C2))
                    worst = min(f, fm) if best is None else None
                    key = (xt, s, str(bv))
                    best = best or {}
                    best[key] = max(f, fm)
        if not best: out.append('%d: nessuna permutazione traducibile' % dl); cnt['nessuna'] += 1; continue
        # per gemello: minimo sulle permutazioni/slot; poi il gemello migliore
        per_tw = collections.defaultdict(list)
        for (xt, s, bv), v in best.items(): per_tw[xt].append(v)
        xt, vals = max(per_tw.items(), key=lambda kv: min(kv[1]))
        verdict = 'TEXTURE_SCAMBIATE' if min(vals) >= 0.99 else 'DIVERSO'
        cnt[verdict] += 1
        out.append('%d gemello %d: %s (min %.3f, max %.3f su %d casi)' % (dl, xt, verdict, min(vals), max(vals), len(vals)))
        print(out[-1], flush=True)
    out.append(str(dict(cnt)))
    print(out[-1])
    open(os.path.join(HERE, 'f6b_sampler_perm.txt'), 'w').write('\n'.join(out) + '\n')


if __name__ == '__main__':
    main()
