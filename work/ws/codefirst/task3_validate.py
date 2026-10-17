"""Task 3 - validazione del risolutore di famiglia con l'ORACOLO PC (luci accese / spente / miste).
Per ogni coppia base (xb, pb) della classe di (xs, pd): T = trapianto di Xb col donatore (xs, pd) e regola di famiglia (f9m.build + mp_resolve),
valutato con i parametri XBOX reali del materiale (T e' nel layout Xbox) e confrontato col PC vero pb valutato con i parametri PC reali.
Uso: task3_validate.py XS PD  -> riga per ogni coppia (incl. unitaria xb=xs)."""
import sys, os, collections
CF = '/path/to/trudlcport/work/ws/codefirst'; sys.path.insert(0, CF)
import f9m
from f9m import *
import mp_resolve, bridge_ext


def compare2(progT, progP, XP, PP, seed=5, bools=None):
    envT = Env(seed, XP); envP = Env(seed, PP)
    a = envT.run(progT, body(progT), envT.state0(progT), bools)
    b = envP.run(progP, body(progP), envP.state0(progP), bools)
    ca, ka = a[0].get((sm3asm.RT_COLOROUT, 0)), a[1]; cb, kb = b[0].get((sm3asm.RT_COLOROUT, 0)), b[1]
    if ca is None or cb is None: return 0.0
    ok = np.isclose(ca, cb, **TOL).all(axis=1) & (ka == kb) | (ka & kb)
    return float(ok.mean())


def virt_env(prog, virt, XP, env):
    """registri virtuali (>=116): compone le lane dai parametri Xbox XP."""
    for vr, spec in virt.items():
        v = np.zeros(4, np.float32)
        for c, src in spec.items():
            v[c] = src[1] if src[0] == 'k' else XP[src[0] - 100][src[1]]
        env.consts[vr] = v


def compare_virt(progT, virt, progP, XP, PP, seed=5, bools=None):
    envT = Env(seed, XP); envP = Env(seed, PP); virt_env(progT, virt, XP, envT)
    a = envT.run(progT, body(progT), envT.state0(progT), bools)
    b = envP.run(progP, body(progP), envP.state0(progP), bools)
    ca, ka = a[0].get((sm3asm.RT_COLOROUT, 0)), a[1]; cb, kb = b[0].get((sm3asm.RT_COLOROUT, 0)), b[1]
    if ca is None or cb is None: return 0.0
    ok = np.isclose(ca, cb, **TOL).all(axis=1) & (ka == kb) | (ka & kb)
    return float(ok.mean())


def one_pair(xb, pb, xs, pd, res, slot=0, nmat=3):
    L = libs(); X, P = L['X'], L['P']
    xblob = X[xb]['entries'][X[xb]['slots'][slot & 1]]['blob']; xsblob = X[xs]['entries'][X[xs]['slots'][slot & 1]]['blob']
    pdblob = P[pd]['entries'][P[pd]['slots'][slot]]['blob']; pbblob = P[pb]['entries'][P[pb]['slots'][slot]]['blob']
    mb = material_pairs(xs, pd); mt = material_pairs(xb, pb)
    if not mb or not mt: raise Fail('nessun materiale ponte/test')
    pbct = pc_ctab(pbblob); xnames = {n: ri for n, rs, ri, rc in pbct if rs == 3}
    log = []
    progT, info = build(xblob, pdblob, xsblob, [(m[2], m[3]) for m in mb], x_samp_names=xnames, log=log, mp_res=res)
    progP = decode_pc(pbblob); out = {}
    for lab, bl in (('on', ALLB), ('off', {}), ('mix', {0: True, 3: True, 6: True})):
        out[lab] = min(compare_virt(progT, info['virt'], progP, m[2], m[3], bools=bl) for m in mt[:nmat])
    return out, info, len(body(progT))


if __name__ == '__main__':
    xs, pd = int(sys.argv[1]), int(sys.argv[2])
    res, ties = mp_resolve.resolve(xs, pd)
    import struct_resolve
    res, ties, _sn = struct_resolve.apply(xs, pd, res, ties)
    print('=== (%d,%d) regola: %d lane, pareggi %d' % (xs, pd, len(res), len(ties)))
    pairs = [(xs, pd)] + [(a, b) for a, b in find_donors('X', xs, 0, want=60) if (a, b) != (xs, pd)]
    for xb, pb in pairs:
        try:
            o, info, n = one_pair(xb, pb, xs, pd, res)
            print('  base (%d,%d): on %.3f off %.3f mix %.3f istr %d virt %d ties %s' % (xb, pb, o['on'], o['off'], o['mix'], n, len(info['virt']), len(info['ties'])), flush=True)
        except Fail as e: print('  base (%d,%d): FAIL %s' % (xb, pb, str(e)[:150]), flush=True)
        except Exception as e: print('  base (%d,%d): ERR %r' % (xb, pb, e)[:200], flush=True)
