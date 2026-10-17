"""F3: validazione del traduttore Xenos->SM3 sul gioco base. Coppie (lib Xbox x, lib PC p=x2p[x]) in posizione 2 (passo colore) NON illuminate.
uso: f3_validate.py [N=50] [seed=1] [--all]"""
import sys, os, struct, collections, random, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from f3_common import *
import xenos_xlat as XL
LIGHT = ('p_Lights', 'LightEnabled', 'p_ShadowEnabled', 'ParallelShadow', 'Irradiance', 'GlobalAmbientColor', 'ShadowLight', 'NonShadow')

def positions():
    L = libs(); XM, PM = L['XM'], L['PM']
    mx2p = pickle.load(open(os.path.join(ROOT, 'work/render/material_x2p.pkl'), 'rb'))
    pos = collections.defaultdict(set)
    for mid, (d, r) in XM.items():
        if mid not in mx2p or mx2p[mid] not in PM: continue
        t = struct.unpack_from('>4I', d, 0x28)
        for i in range(3):
            if t[i]: pos[t[i]].add(i)
    return pos

def xbox_info(x):
    L = libs(); lib = L['X'][x]
    names = set(); slots = []
    for s in lib['slots']:
        if s == 0xffffffff: slots.append(None); continue
        blob = lib['entries'][s]['blob']
        sh = XL.parse(blob)
        slots.append(sh)
        for c in sh.ctab: names.add((c['name'], c['set']))
    return slots, names

def candidates():
    L = libs(); pos = positions(); out = []
    pcn = pc_names()
    for x, p in sorted(x2p().items()):
        if L['X'][x]['kind'] != 1 or pos.get(x) != {2}: continue
        slots, names = xbox_info(x)
        if any(any(k in n for k in LIGHT) for n, _ in names): continue
        fl = [n for n, st in names if st == 2]
        if any(n not in pcn for n in fl): continue
        if any(st == 0 for n, st in names): continue      # bool: permutazioni dinamiche, escluso
        out.append((x, p))
    return out

def run_pair(x, p, samp_mode='identity'):
    L = libs(); X, P = L['X'], L['P']
    res = []
    for xs in (0, 1):
        s = X[x]['slots'][xs]
        blob = X[x]['entries'][s]['blob']
        sh = XL.parse(blob)
        ks = [k for k in range(len(P[p]['slots'])) if (k & 1) == xs and P[p]['slots'][k] != 0xffffffff]
        if not ks and xs == 1: res.append(('NOPCSLOT', 'PC non ha slot dispari (solo slot Xbox 0 usato)')); continue
        if not ks: res.append(('NOPCSLOT', 'nessuno slot PC con bit0=%d' % xs)); continue
        pslot = P[p]['slots'][ks[0]]
        pb = P[p]['entries'][pslot]['blob']
        pprog = pc_prog(pb)
        samp = None
        if samp_mode == 'twin':
            twin = {n: r for n, rs, r, c in ctab_pc(pb) if rs == 3}
            samp = lambda name, cidx: twin.get(name, cidx)
        else:
            samp = lambda name, cidx: cidx
        try:
            tr = xenos2sm3.translate(blob, const_fn, samp=samp)
        except xenos2sm3.Reject as e:
            res.append(('REJECT', str(e))); continue
        try:
            prog = sm3asm.parse_text(tr.text)
            sm3asm.encode(prog)
        except Exception as e:
            res.append(('ASMERR', repr(e)[:100], tr.text)); continue
        try:
            r = compare(prog, pprog)
        except Exception as e:
            res.append(('VMERR', repr(e)[:100], tr.text)); continue
        # registri costanti/sampler/dcl
        pin, _ = inputs_of(pprog); tin, _ = inputs_of(prog)
        defs_t = set(o.ops[0].num for o in prog.instrs() if o.op == 'def')
        defs_p = set(o.ops[0].num for o in pprog.instrs() if o.op == 'def')
        ct = set(r_ for r_ in r['usedA'] if r_ not in defs_t); cp = set(r_ for r_ in r['usedB'] if r_ not in defs_p)
        res.append(('OK', r['frac'], dict(consts_eq=ct == cp, ct=sorted(ct), cp=sorted(cp), samp_eq=r['sampA'] == r['sampB'], sa=sorted(r['sampA']), sb=sorted(r['sampB']),
                                           dcl_eq=tin == pin, tin={str(k): sorted(v) for k, v in tin.items()}, pin={str(k): sorted(v) for k, v in pin.items()}), tr.text))
    return res

if __name__ == '__main__':
    N = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 50
    seed = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 1
    cands = candidates()
    print('candidati pos2 non illuminati:', len(cands))
    random.seed(seed)
    sel = cands if '--all' in sys.argv else random.sample(cands, min(N, len(cands)))
    mode = 'twin' if '--twin' in sys.argv else 'identity'
    tab = []
    for x, p in sel:
        rs = run_pair(x, p, mode)
        tab.append((x, p, rs))
    json.dump([(x, p, [r[:3] if r[0] == 'OK' else r[:2] for r in rs]) for x, p, rs in tab], open(os.path.join(HERE, 'f3_result_%s.json' % mode), 'w'), indent=1, default=str)
    cnt = collections.Counter()
    for x, p, rs in tab:
        kinds = tuple(r[0] if r[0] != 'OK' else ('PASS' if r[1] >= 0.95 else 'LOWSIM') for r in rs)
        cnt[kinds] += 1
    print(cnt)
    for x, p, rs in tab:
        for i, r in enumerate(rs):
            if r[0] != 'OK': print(x, p, i, r[0], r[1])
            else: print(x, p, i, 'OK frac=%.3f' % r[1], 'consts_eq' if r[2]['consts_eq'] else 'consts %s vs %s' % (r[2]['ct'], r[2]['cp']), 'samp_eq' if r[2]['samp_eq'] else 'samp %s vs %s' % (r[2]['sa'], r[2]['sb']), 'dcl_eq' if r[2]['dcl_eq'] else 'dcl %s vs %s' % (r[2]['tin'], r[2]['pin']))
