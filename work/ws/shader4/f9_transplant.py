"""F9 - TRAPIANTO luci: shader Xbox illuminato X (tradotto) + blocco luci PC copiato da un donatore Pd (PS PC), con il gemello Xbox Xs
di Pd come ponte per abbinare ingressi/uscite.

  T = [pre di X tradotto] + [mov ingressi Pd <- valori di X] + [catena `if bN` di Pd, temp/v rinominati] + [mov uscite X <- Pd] + [post di X]

Abbinamenti (tutti numerici, sull'interprete sm3vm):
  Pd.in  <-> Xs.in   : valori uguali dopo le parti "pre" con i parametri reali di un materiale base (Xbox e PC hanno lo stesso layout
                       MaterialParams per gli illuminati); ingressi PC costanti -> def
  Pd.out <-> Xs.out  : impronte sulle parti "post" (stesso valore di base in tutte le uscite, una perturbata per volta)
  Xs.in/out <-> X.in/out : impronte sui blocchi luci Xbox (stesso modello: stessa funzione a meno di permutazioni)
ORACOLO (gioco base): X = lib Xbox base Xb, confronto di T con il gemello PC vero Pb (parametri reali del materiale, luci casuali,
bool delle luci accesi/spenti). Test unitario: Pd = Pb (deve dare 1.0). Test vero: Pd = un altro PC della stessa famiglia.

uso: tools/venv/bin/python -I work/ws/shader4/f9_transplant.py oracolo [N_coppie=30] [seme=1]
     tools/venv/bin/python -I work/ws/shader4/f9_transplant.py coppia XB PB PD   (diagnostica di una coppia)
uscita: work/ws/shader4/f9_oracolo.tsv + f9_oracolo.md"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from f9_common import *

N = 300
ALIAS = {'CameraPosition': 'g_CameraPosition', 'TimeVector': 'TimeVectorPS', 'GlobalAmbientColor': 'g_Ambient'}
TOL = dict(rtol=1e-3, atol=1e-4)


class Fail(Exception):
    pass


# ---------------------------------------------------------------------------------------------- costanti e sampler
class Consts:
    """nome Xbox -> registro PC: tabella del donatore (nomi PC, alias) + MaterialParams c100+j; i nomi solo-Xbox prendono registri liberi
    e vengono annotati (se letti fuori dal blocco luci il trapianto non e' valido sul PC)."""
    def __init__(self, pct):
        self.pfl = {n: (ri, rc) for n, rs, ri, rc in pct if rs == 2}
        for n, regs in pc_names().items():                    # nomi PC del gioco base (registro fisso piu' frequente)
            if n not in self.pfl: self.pfl[n] = (regs[0][0][0], regs[0][0][1])
        used = set(r for (ri, rc) in self.pfl.values() for r in range(ri, ri + rc))
        self.free = [r for r in range(6, 224) if r not in used and not 100 <= r < 116]
        self.extra = {}

    def fn(self, name, j, count):
        n2 = ALIAS.get(name, name)
        if n2 in self.pfl: return self.pfl[n2][0] + j
        if name == 'MaterialParams': return 100 + j
        k = (name, j)
        if k not in self.extra:
            if not self.free: return None
            self.extra[k] = self.free.pop(0)
        return self.extra[k]


def xsamp(xblob, regs_by_name):
    sm = {c['reg']: c['name'] for c in XL.parse(xblob).ctab if c['set'] == 3}
    def f(name, c):
        n = sm.get(c, name)
        if regs_by_name is None: return c
        if isinstance(regs_by_name, tuple):                 # ('globali', preg): texture del materiale per registro, globali per nome
            return c if n.startswith('p_default') else regs_by_name[1].get(n, c)
        return regs_by_name.get(n, regs_by_name.get(norm_x(n), c))
    return f


def norm_x(n): return re.sub(r'_[0-9A-F]{12,18}(?=_|$)', '_#', n)


def xbools(blob):
    sh = XL.parse(blob)
    return {n: (0 if n == 'p_ShadowEnabled' else 1) for n in set(bool_names(sh).values())}


def decode_pc(blob):
    return sm3asm.decode(blob[:sm3dis.bytecode_len(blob)])


# ---------------------------------------------------------------------------------------------- esecuzione
class Env:
    def __init__(self, seed=1, matp=None, N=N):
        rng = np.random.RandomState(seed); self.N = N; self.rng = rng
        self.vals = {(u, i): rng.uniform(0, 1, (N, 4)).astype(np.float32) for u in range(16) for i in range(16)}
        self.consts = {r: rng.uniform(0.05, 1.5, 4).astype(np.float32) for r in range(224)}
        if matp is not None:
            for j, v in enumerate(matp): self.consts[100 + j] = np.array(v, np.float32)
        self.tex = sm3vm.det_tex(lambda s: s)
        self.u = rng.uniform(0, 1, N).astype(np.float32); self.d = rng.uniform(0.1, 0.5, N).astype(np.float32)

    def state0(self, prog):
        return semantic_inputs(prog, self.vals)

    def run(self, prog, instrs, state, bools=None):
        return run_state(prog, instrs, state, self.consts, self.tex, self.N, bools)


ALLB = {b: True for b in range(16)}


def col(st, r, c):
    v = st.get((0, r)); return None if v is None else v[:, c]


def inject(st, comps, u, pert=None, N=N, consts=None):
    """comps: (r, c) temp o ('c', r, c) costante. Ritorna lo stato (e, se consts e' dato, le costanti modificate)."""
    s2 = {k: v.copy() for k, v in st.items()}
    c2 = None if consts is None else dict(consts)
    def put(item, val, add=False):
        if len(item) == 3:
            _, r, c = item
            a = np.array(np.broadcast_to(c2[r], (N, 4)), np.float32)
            a[:, c] = (a[:, c] + val) if add else val; c2[r] = a
        else:
            r, c = item
            s2.setdefault((0, r), np.zeros((N, 4), np.float32))
            s2[(0, r)][:, c] = (s2[(0, r)][:, c] + val) if add else val
    for it in comps: put(it, u if np.ndim(u) else u)
    if pert: put(pert[0], pert[1], add=True)
    return s2 if consts is None else (s2, c2)


def fingerprints(prog, a, b, ins, outs, env, bools=None, base_state=None):
    """stesso valore u in tutti gli ingressi; perturba un ingresso per volta -> {ingresso: {uscita: delta}}"""
    st = base_state if base_state is not None else env.state0(prog)
    B = body(prog)
    def go(pert):
        s2, c2 = inject(st, ins, env.u, pert, consts=env.consts)
        return run_state(prog, B[a:b], s2, c2, env.tex, env.N, bools)[0]
    r0 = go(None)
    fp = {}
    for i in ins:
        r1 = go((i, env.d))
        fp[i] = {o: r1.get((0, o[0]), np.zeros((env.N, 4)))[:, o[1]] - r0.get((0, o[0]), np.zeros((env.N, 4)))[:, o[1]] for o in outs}
    base = {o: r0.get((0, o[0]), np.zeros((env.N, 4)))[:, o[1]] for o in outs}
    return fp, base


def match_blocks(pA, a0, a1, inA, outA, pB, b0, b1, inB, outB, env, max_try=3000):
    """blocchi Xbox A (X) e B (ponte) con la stessa funzione a meno di permutazioni: ritorna (inB->inA, outB->outA) verificati
    (verify_blocks >= 0.99); le ambiguita' delle impronte si risolvono provando le combinazioni."""
    fA, baseA = fingerprints(pA, a0, a1, inA, outA, env)
    fB, baseB = fingerprints(pB, b0, b1, inB, outB, env)
    def dset(f, o): return [v for v in (f[i][o] for i in f) if np.abs(v).max() > 1e-6]
    def same_multiset(da, db):
        if len(da) != len(db): return False
        used = set()
        for x in db:
            k = next((k for k, y in enumerate(da) if k not in used and np.allclose(x, y, **TOL)), None)
            if k is None: return False
            used.add(k)
        return True
    ocand = {ob: [oa for oa in outA if np.allclose(baseA[oa], baseB[ob], **TOL) and same_multiset(dset(fA, oa), dset(fB, ob))] for ob in outB}
    if any(not v for v in ocand.values()): raise Fail('uscite del blocco ponte senza candidati: %s' % [k for k, v in ocand.items() if not v])
    tries = 0
    obs = list(outB)
    def omaps(k, cur):
        if k == len(obs): yield dict(cur); return
        for oa in ocand[obs[k]]:
            if oa in cur.values(): continue
            cur[obs[k]] = oa; yield from omaps(k + 1, cur); del cur[obs[k]]
    for om in omaps(0, {}):
        icand = {}
        for ib in inB:
            infl = any(np.abs(fB[ib][o]).max() > 1e-6 for o in outB)
            kind = len(ib)
            if infl: icand[ib] = [ia for ia in inA if len(ia) == kind and all(np.allclose(fA[ia][om[o]], fB[ib][o], **TOL) for o in outB)]
            else: icand[ib] = [ia for ia in inA if len(ia) == kind and all(np.abs(fA[ia][om[o]]).max() <= 1e-6 for o in outB)]
        if any(not v for v in icand.values()): continue
        ibs = sorted(inB, key=lambda i: len(icand[i]))
        def imaps(k, cur):
            if k == len(ibs): yield dict(cur); return
            for ia in icand[ibs[k]]:
                if ia in cur.values(): continue
                cur[ibs[k]] = ia; yield from imaps(k + 1, cur); del cur[ibs[k]]
        for im in imaps(0, {}):
            tries += 1
            if verify_blocks(pA, a0, a1, inA, outA, pB, b0, b1, inB, outB, im, om, env) >= 0.99: return im, om
            if tries >= max_try: raise Fail('abbinamento blocchi: troppe combinazioni')
    raise Fail('blocchi non equivalenti (nessuna combinazione verificata, %d prove)' % tries)


def verify_blocks(pA, a0, a1, inA, outA, pB, b0, b1, inB, outB, imap, omap, env):
    """ingressi casuali indipendenti (abbinati uguali): frazione di campioni con uscite abbinate uguali."""
    rng = np.random.RandomState(9); vals = {i: rng.uniform(0, 1, env.N).astype(np.float32) for i in inB}
    sA, cA = inject(env.state0(pA), [], 0, consts=env.consts); sB, cB = inject(env.state0(pB), [], 0, consts=env.consts)
    for ia in inA:
        ib = next((k for k, v in imap.items() if v == ia), None)
        v = vals[ib] if ib is not None else rng.uniform(0, 1, env.N).astype(np.float32)
        sA, cA = inject(sA, [ia], v, consts=cA)
    for ib in inB: sB, cB = inject(sB, [ib], vals[ib], consts=cB)
    rA = run_state(pA, body(pA)[a0:a1], sA, cA, env.tex, env.N)[0]; rB = run_state(pB, body(pB)[b0:b1], sB, cB, env.tex, env.N)[0]
    ok = np.ones(env.N, bool)
    for ob, oa in omap.items():
        ok &= np.isclose(rA.get((0, oa[0]), np.zeros((env.N, 4)))[:, oa[1]], rB.get((0, ob[0]), np.zeros((env.N, 4)))[:, ob[1]], **TOL)
    return float(ok.mean())


def mp_reads(prog, a, b):
    st = stypes(prog); out = set()
    for i in body(prog)[a:b]:
        for j, o in enumerate(i.ops):
            if not o.isdst and o.rtype == sm3asm.RT_CONST and 100 <= o.num < 116:
                for c in lanes(i, j, st): out.add((o.num, c))
    return out


# ---------------------------------------------------------------------------------------------- costruzione
def build(xblob, pdblob, xsblob, bridge, xs_samp_names=None, x_samp_names=None, pd_slot_bools=None, log=None, x_opts=None):
    """Ritorna (testo SM3 di T, info). bridge = (XP, PP) del materiale ponte (Xs/Pd)."""
    log = log if log is not None else []
    ZERO_OUTS[:] = []
    pprog = decode_pc(pdblob); pct = pc_ctab(pdblob)
    preg = {n: ri for n, rs, ri, rc in pct if rs == 3}
    K = Consts(pct)
    xprog, i0, i1, trx = translate_x(xblob, K.fn, xsamp(xblob, x_samp_names if x_samp_names is not None else ('globali', preg)), xbools(xblob), opts=x_opts)
    sprog, s0, s1, trs = translate_x(xsblob, K.fn, xsamp(xsblob, preg), xbools(xsblob))
    p0, p1 = pc_light_block(pprog)
    if i0 is None or s0 is None or p0 is None: raise Fail('blocco luci non trovato (X %s, Xs %s, Pd %s)' % (i0, s0, p0))
    xin, xout = live_in_out(xprog, i0, i1); sin, sout = live_in_out(sprog, s0, s1); pin, pout = live_in_out(pprog, p0, p1)
    log.append('blocchi X[%d,%d) in %d out %d | Xs[%d,%d) in %d out %d | Pd[%d,%d) in %d out %d' % (i0, i1, len(xin), len(xout), s0, s1, len(sin), len(sout), p0, p1, len(pin), len(pout)))
    # costanti solo-Xbox lette fuori dal blocco in X: non esistono sul PC
    extra_regs = set(K.extra.values())
    st_x = stypes(xprog)
    bad = sorted({o.num for k, i in enumerate(body(xprog)) if not i0 <= k < i1 for o in i.ops if not o.isdst and o.rtype == sm3asm.RT_CONST and o.num in extra_regs})
    if bad:
        inv = {v: k for k, v in K.extra.items()}
        raise Fail('X legge costanti solo-Xbox fuori dal blocco: %s' % sorted(set(inv[r][0] for r in bad)))
    # parametri materiale letti dai blocchi = ingressi aggiuntivi
    mx, ms, mpd = mp_reads(xprog, i0, i1), mp_reads(sprog, s0, s1), mp_reads(pprog, p0, p1)
    xin_all = list(xin) + [('c',) + m for m in sorted(mx)]; sin_all = list(sin) + [('c',) + m for m in sorted(ms)]
    # ---- ponte Pd <-> Xs (materiale reale). Le texture lette solo da Xs (il porting PC le ha tolte) si provano neutre: 0.5, 1, 0.
    if isinstance(bridge, list): BRIDGES = bridge; XP, PP = bridge[0]
    else: XP, PP = bridge; BRIDGES = [bridge]
    pd_samp = {o.num for i in body(pprog) for o in i.ops if o.rtype == sm3asm.RT_SAMPLER}
    xs_only = {o.num for i in body(sprog) for o in i.ops if o.rtype == sm3asm.RT_SAMPLER} - pd_samp
    last_err = None
    for neutral in ((None,) if not xs_only else (0.5, 1.0, 0.0)):
        envx = Env(1, XP); envp = Env(1, PP)
        base_tex = envx.tex
        if neutral is not None:
            envx.tex = (lambda bt, nv: (lambda smp, c, m: np.full((c.shape[0], 4), nv, np.float32) if smp in xs_only else bt(smp, c, m)))(base_tex, neutral)
        envp.vals = envx.vals; envp.tex = base_tex
        for r in range(224):
            if not 100 <= r < 116: envp.consts[r] = envx.consts[r]
        sts, _ = envx.run(sprog, body(sprog)[:s0], envx.state0(sprog))
        stp, _ = envp.run(pprog, body(pprog)[:p0], envp.state0(pprog), ALLB)
        p_from_s = {}; p_const = {}
        def group_match(r):
            """livello largo: tutte le componenti del registro Pd r -> stesso registro Xs, componente per componente (corr >= 0.6, margine 0.1)"""
            comps = [(rr, cc) for (rr, cc) in pin if rr == r]
            best = {}
            for (rr, cc) in comps:
                a_ = col(stp, rr, cc)
                if a_ is None or np.std(a_) < 1e-6: return None
                sc_ = sorted(((float(np.corrcoef(a_, col(sts, rs, cs))[0, 1]), (rs, cs)) for (rs, cs) in sin
                              if col(sts, rs, cs) is not None and np.std(col(sts, rs, cs)) > 1e-6), reverse=True)
                if not sc_ or sc_[0][0] < 0.6 or (len(sc_) > 1 and sc_[0][0] - sc_[1][0] < 0.1): return None
                best[(rr, cc)] = sc_[0]
            regs = {v[1][0] for v in best.values()}
            if len(regs) != 1 or len({v[1] for v in best.values()}) != len(best): return None
            return best
        try:
            for (r, c) in pin:
                if (r, c) in p_from_s: continue
                a = col(stp, r, c)
                hits = [(rs, cs) for (rs, cs) in sin if col(sts, rs, cs) is not None and np.allclose(a, col(sts, rs, cs), **TOL)]
                if hits: p_from_s[(r, c)] = hits[0]
                elif np.allclose(a, a[0], **TOL): p_const[(r, c)] = float(a[0])
                else:
                    sc = []
                    for (rs, cs) in sin:
                        b = col(sts, rs, cs)
                        if b is None or np.std(b) < 1e-6 or np.std(a) < 1e-6: continue
                        sc.append((float(np.corrcoef(a, b)[0, 1]), (rs, cs)))
                    sc.sort(reverse=True)
                    if sc and sc[0][0] >= 0.98 and (len(sc) == 1 or sc[0][0] - sc[1][0] >= 0.02):
                        p_from_s[(r, c)] = sc[0][1]
                        log.append('ingresso Pd r%d.%s abbinato per correlazione %.3f a Xs r%d.%s' % (r, 'xyzw'[c], sc[0][0], sc[0][1][0], 'xyzw'[sc[0][1][1]]))
                    else:
                        gm = group_match(r)
                        if gm is None:
                            raise Fail('ingresso Pd r%d.%s senza corrispondente nel ponte (migliore correlazione %s)' % (r, 'xyzw'[c], ['%.3f' % v for v, _ in sc[:2]]))
                        for k_, (v_, t_) in gm.items():
                            p_from_s[k_] = t_
                        log.append('APPROSSIMATO: Pd r%d -> Xs r%d per gruppo (corr %s)' % (r, list(gm.values())[0][1][0], ['%.2f' % v_ for v_, _ in gm.values()]))
            if neutral is not None: log.append('ponte: texture solo-Xbox %s neutre a %g' % (sorted(xs_only), neutral))
            last_err = None
            break
        except Fail as e:
            last_err = e
    if last_err is not None: raise last_err
    # uscite Pd <-> Xs via post
    def post_fp(prog, st, outs, i1_, env, bools=None):
        B = body(prog)
        base, _ = env.run(prog, B[i1_:], inject(st, outs, env.u), bools)
        fp = {}
        for o in outs:
            r1, _ = env.run(prog, B[i1_:], inject(st, outs, env.u, (o, env.d)), bools)
            fp[o] = r1.get((sm3asm.RT_COLOROUT, 0)) - base.get((sm3asm.RT_COLOROUT, 0))
        return fp, base.get((sm3asm.RT_COLOROUT, 0))
    fs, bs = post_fp(sprog, sts, sout, s1, envx); fpp, bp = post_fp(pprog, stp, pout, p1, envp, ALLB)
    post_eq = float(np.isclose(bs, bp, **TOL).all(axis=1).mean())
    log.append('post Xs vs Pd (uscite blocco iniettate uguali): %.3f' % post_eq)
    p_to_s_out = {}; pend = []
    for o, dp in fpp.items():
        if np.abs(dp).max() <= 1e-6: continue
        hits = [os_ for os_, dx in fs.items() if np.allclose(dp, dx, **TOL)]
        if len(hits) == 1: p_to_s_out[o] = hits[0]
        else: pend.append(o)
    # uscite non abbinate esattamente (parte finale PC semplificata): correlazione delle impronte sul colore finale, per gruppo di registro
    def corr(a_, b_):
        a_ = np.nan_to_num(a_).ravel(); b_ = np.nan_to_num(b_).ravel()
        return float(np.corrcoef(a_, b_)[0, 1]) if np.std(a_) > 1e-9 and np.std(b_) > 1e-9 else -1.0
    for r in sorted({o[0] for o in pend}):
        grp = [o for o in pend if o[0] == r]
        used = set(p_to_s_out.values())
        cands = []
        for R in sorted({os_[0] for os_ in fs}):
            comps = [os_ for os_ in fs if os_[0] == R and os_ not in used]
            if len(comps) < len(grp): continue
            best_perm, best_sc = None, -9
            for perm in itertools.permutations(comps, len(grp)):
                sc_ = float(np.mean([corr(fpp[o], fs[t]) for o, t in zip(grp, perm)]))
                if sc_ > best_sc: best_sc, best_perm = sc_, perm
            cands.append((best_sc, R, best_perm))
        cands.sort(reverse=True)
        if not cands or cands[0][0] < 0.85 or (len(cands) > 1 and cands[0][0] - cands[1][0] < 0.03):
            raise Fail('uscite Pd r%d: nessun registro corrispondente nel ponte (migliori %s)' % (r, ['%.2f' % c_[0] for c_ in cands[:2]]))
        for o, t in zip(grp, cands[0][2]): p_to_s_out[o] = t
        log.append('APPROSSIMATO: uscite Pd r%d -> Xs r%d (corr media %.2f, secondo %s)' % (r, cands[0][1], cands[0][0], '%.2f' % cands[1][0] if len(cands) > 1 else '-'))
    # ---- Xs <-> X (blocchi Xbox)
    envb = Env(2)
    imap, omap = match_blocks(xprog, i0, i1, xin_all, xout, sprog, s0, s1, sin_all, sout, envb)
    veq = verify_blocks(xprog, i0, i1, xin_all, xout, sprog, s0, s1, sin_all, sout, imap, omap, envb)
    log.append('blocchi Xbox X vs ponte dopo abbinamento: %.3f' % veq)
    if veq < 0.99: raise Fail('blocco luci di X non equivalente a quello del ponte (%.3f)' % veq)
    # letture MaterialParams del blocco PC: Pd -> Xs (stesso valore nel materiale ponte) -> X
    mp_remap = {}
    for (r, c) in sorted(mpd):
        v = PP[r - 100][c] if r - 100 < len(PP) else None
        cands = [m for m in sorted(ms) if v is not None and m[0] - 100 < len(XP) and abs(XP[m[0] - 100][m[1]] - v) < 1e-6]
        if (r, c) in cands: cands = [(r, c)]
        if len(cands) > 1:
            # ambiguo nel primo materiale ponte: interseca con gli altri materiali che usano la stessa coppia di lib
            for XP2, PP2 in BRIDGES[1:]:
                v2 = PP2[r - 100][c] if r - 100 < len(PP2) else None
                if v2 is None: continue
                cands = [m for m in cands if m[0] - 100 < len(XP2) and abs(XP2[m[0] - 100][m[1]] - v2) < 1e-6]
                if len(cands) <= 1: break
        if len(cands) > 1:
            # ancora ambiguo: perturba il parametro nel blocco Pd e ciascun candidato nel blocco Xs, confronta le variazioni delle uscite
            def blk_delta(prog, a0, a1, st, env, item, outs_map, bools=None):
                c0 = dict(env.consts)
                r0 = run_state(prog, body(prog)[a0:a1], st, c0, env.tex, env.N, bools)[0]
                c1 = dict(c0); v_ = np.array(np.broadcast_to(c1[item[0]], (env.N, 4)), np.float32); v_[:, item[1]] += 0.3; c1[item[0]] = v_
                r1 = run_state(prog, body(prog)[a0:a1], st, c1, env.tex, env.N, bools)[0]
                return {k: r1.get((0, k[0]), np.zeros((env.N, 4)))[:, k[1]] - r0.get((0, k[0]), np.zeros((env.N, 4)))[:, k[1]] for k in outs_map}
            st_p = inject(stp, [], 0); st_s = inject(sts, [], 0)
            dp_ = blk_delta(pprog, p0, p1, st_p, envp, (r, c), list(p_to_s_out.keys()), ALLB)
            good = []
            for m in cands:
                ds_ = blk_delta(sprog, s0, s1, st_s, envx, m, list(p_to_s_out.values()))
                if all(np.allclose(dp_[po], ds_[so], rtol=1e-2, atol=1e-3) for po, so in p_to_s_out.items()) and any(np.abs(dp_[po]).max() > 1e-5 for po in p_to_s_out):
                    good.append(m)
            if len(good) == 1: cands = good
            elif not good and all(np.abs(dp_[po]).max() <= 1e-5 for po in p_to_s_out): cands = cands[:1]   # parametro senza effetto sulle uscite
        if len(cands) != 1: raise Fail('MaterialParams c%d.%s del blocco PC: %d corrispondenti nel ponte' % (r, 'xyzw'[c], len(cands)))
        tgt = imap.get(('c',) + cands[0])
        if tgt is None: raise Fail('MaterialParams %s del ponte senza corrispondente in X' % (cands[0],))
        mp_remap[(r, c)] = (tgt[1], tgt[2])
    # ---- composizione
    in_moves = []
    for p, s in p_from_s.items():
        if s not in imap: raise Fail('ingresso ponte %s non abbinato in X' % (s,))
        in_moves.append((p, imap[s]))
    log.append('MaterialParams blocco PC -> X: %s' % {('c%d.%s' % (r, 'xyzw'[c])): ('c%d.%s' % (t[0], 'xyzw'[t[1]])) for (r, c), t in mp_remap.items()})
    out_moves = []
    for p, s in p_to_s_out.items():
        if s not in omap: raise Fail('uscita ponte %s non abbinata in X' % (s,))
        out_moves.append((omap[s], p))
    missing = set(xout) - {x for x, _ in out_moves}
    sl = []
    if missing:
        # uscite del blocco Xbox che il blocco PC non produce: si copia la fetta Xbox che le calcola, se non usa luci
        sl = backslice(xprog, i0, i1, missing)
        reads_extra = {o.num for i in sl for o in i.ops if not o.isdst and o.rtype == sm3asm.RT_CONST and o.num in extra_regs}
        if reads_extra:
            # il blocco luci PC del donatore non produce questa uscita (es. speculare tolta dal porting): zero, come il PC
            ZERO_OUTS[:] = sorted(missing); sl = []
            log.append('uscite %s di X senza valore PC (dipendono da luci Xbox): messe a 0 come nel blocco PC' % (sorted(missing),))
        else:
            log.append('uscite %s calcolate con la fetta Xbox (%d istruzioni, senza luci)' % (sorted(missing), len(sl)))
    return assemble(xprog, i0, i1, pprog, p0, p1, in_moves, p_const, out_moves, xin, xout, log, mp_remap, sl), dict(log=log, post_eq=post_eq)


ZERO_OUTS = []


def backslice(prog, a, b, comps):
    """istruzioni di body[a:b] necessarie a calcolare le componenti temp 'comps' alla fine dell'intervallo (lineare)."""
    B = body(prog)[a:b]; st = stypes(prog); live = set(comps); keep = []
    for i in reversed(B):
        if i.op in ('if', 'ifc', 'else', 'endif', 'texkill'): continue
        if not (i.ops and i.ops[0].isdst and i.ops[0].rtype == sm3asm.RT_TEMP): continue
        w = {(i.ops[0].num, c) for c in range(4) if i.ops[0].wm >> c & 1}
        if not (w & live): continue
        keep.append(i); live -= w
        for j, o in enumerate(i.ops):
            if not o.isdst and o.rtype == sm3asm.RT_TEMP:
                for c in lanes(i, j, st): live.add((o.num, c))
    return list(reversed(keep))


def assemble(xprog, i0, i1, pprog, p0, p1, in_moves, p_const, out_moves, xin, xout, log, mp_remap=None, xslice=()):
    mp_remap = mp_remap or {}
    BX, BP = body(xprog), body(pprog)
    # v-registri: Pd -> X per semantica
    xin_sem, xv = inputs_of(xprog); pin_sem, pv = inputs_of(pprog)
    vmap = {}; xvinv = {v: s for s, v in xv.items()}; next_v = max(list(xv.values()) + [-1]) + 1; extra_dcl = []
    for s, v in pv.items():
        if s[0] == 'misc': continue
        if s in xv: vmap[v] = xv[s]
        else:
            vmap[v] = next_v; extra_dcl.append((s, next_v)); next_v += 1
    # registri temp: riservati quelli di X letti dopo il blocco, ingressi e uscite del blocco X
    reserved = set(r for r, _ in xin if not isinstance(r, str)) | set(r for r, _ in xout)
    reserved |= {i.ops[0].num for i in xslice}
    for i in BX[i1:]:
        for o in i.ops:
            if not o.isdst and o.rtype == sm3asm.RT_TEMP: reserved.add(o.num)
    ptemps = sorted({o.num for i in BP[p0:p1] for o in i.ops if o.rtype == sm3asm.RT_TEMP} | {r for r, _ in [m[0] for m in in_moves]} | set(r for r, _ in p_const) | {p[0] for _, p in out_moves})
    free = [r for r in range(32) if r not in reserved]
    if len(free) < len(ptemps): raise Fail('temp insufficienti: servono %d, liberi %d' % (len(ptemps), len(free)))
    tmap = dict(zip(ptemps, free))
    # costanti: def di Pd letti nel blocco; conflitti con registri usati da X
    xconst_used = {o.num for i in BX for o in i.ops if o.rtype == sm3asm.RT_CONST} | {i.ops[0].num for i in header(xprog) if i.op == 'def'}
    pdefs = {i.ops[0].num: i for i in header(pprog) if i.op == 'def'}
    pblock_c = {o.num for i in BP[p0:p1] for o in i.ops if o.rtype == sm3asm.RT_CONST}
    cmap = {}
    free_c = [r for r in range(223, 0, -1) if r not in xconst_used and r not in pblock_c]
    for r in sorted(pblock_c & set(pdefs)):
        cmap[r] = r if r not in xconst_used else free_c.pop(0)
    lines = ['ps_3_0']
    xtext = sm3asm.format_program(xprog).splitlines()
    xhead = [l for l in xtext[1:] if l.split()[0] in ('dcl', 'def') or l.startswith('dcl_')]
    lines += xhead
    for s, v in extra_dcl:
        uname = {10: 'color', 5: 'texcoord', 0: 'position'}.get(s[0])
        if uname is None: raise Fail('semantica d\'ingresso Pd non gestita %s' % (s,))
        comps = ''.join('xyzw'[c] for c in sorted(pin_sem[s]))
        lines.append('dcl_%s%s v%d.%s' % (uname, s[1] if s[1] else '', v, comps))
    have_samp = {int(l.split()[1][1:]) for l in xhead if l.startswith('dcl_') and l.split()[1].startswith('s')}
    ptext = sm3asm.format_program(pprog).splitlines()
    for l in ptext[1:]:
        if l.startswith('dcl_') and ' s' in l:
            n = int(l.split()[1][1:])
            if any(o.rtype == sm3asm.RT_SAMPLER and o.num == n for i in BP[p0:p1] for o in i.ops):
                if n in have_samp:
                    xl = next(x for x in xhead if x.startswith('dcl_') and x.split()[1] == 's%d' % n)
                    if xl.split()[0] != l.split()[0]: raise Fail('sampler s%d usato da X e dal blocco PC con tipi diversi' % n)
                else: lines.append(l)
    for r, i in pdefs.items():
        if r in cmap: lines.append('def c%d, %s' % (cmap[r], ', '.join('%.9g' % struct.unpack('<f', struct.pack('<I', u))[0] for u in i.imm)))
    kdef = {}
    for (r, c), v in p_const.items():
        if v not in kdef:
            kdef[v] = free_c.pop(0); lines.append('def c%d, %.9g, %.9g, %.9g, %.9g' % (kdef[v], v, v, v, v))
    xbody = [sm3asm.fmt_instr(i, 'ps') for i in BX]
    lines += xbody[:i0]
    for (p, x) in in_moves:
        lines.append('mov r%d.%s, r%d.%s' % (tmap[p[0]], 'xyzw'[p[1]], x[0], 'xyzw'[x[1]]))
    for (r, c), v in p_const.items():
        lines.append('mov r%d.%s, c%d.x' % (tmap[r], 'xyzw'[c], kdef[v]))
    lines += [sm3asm.fmt_instr(i, 'ps') for i in xslice]
    zdef = None
    for (r, c) in ZERO_OUTS:
        if zdef is None:
            zdef = free_c.pop(0); lines.insert(1, 'def c%d, 0, 0, 0, 0' % zdef)
        lines.append('mov r%d.%s, c%d.x' % (r, 'xyzw'[c], zdef))
    for i in BP[p0:p1]:
        j = sm3asm.Instr(i.op, [], i.ctrl, i.pred, i.imm, i.usage)
        ops = []
        for o in i.ops:
            o2 = sm3asm.Operand(o.rtype, o.num, o.isdst, o.rel, o.relop, o.wm, o.mod, o.shift, o.swz, o.smod, o.resv)
            if o.rtype == sm3asm.RT_TEMP: o2.num = tmap[o.num]
            elif o.rtype == sm3asm.RT_INPUT: o2.num = vmap.get(o.num, o.num)
            elif o.rtype == sm3asm.RT_CONST and o.num in cmap: o2.num = cmap[o.num]
            elif o.rtype == sm3asm.RT_CONST and not o.isdst and any(k[0] == o.num for k in mp_remap):
                used = lanes(i, i.ops.index(o), stypes(pprog))
                tg = {mp_remap[(o.num, c)] for c in used if (o.num, c) in mp_remap}
                if len({t[0] for t in tg}) != 1 or any((o.num, c) not in mp_remap for c in used):
                    raise Fail('lettura MaterialParams c%d non rimappabile su un solo registro' % o.num)
                newr = next(iter(tg))[0]; sw = [(o.swz >> (2 * l)) & 3 for l in range(4)]
                sw = [mp_remap[(o.num, c)][1] if (o.num, c) in mp_remap else c for c in sw]
                o2.num = newr; o2.swz = sum(c << (2 * l) for l, c in enumerate(sw))
            ops.append(o2)
        j.ops = ops
        lines.append(sm3asm.fmt_instr(j, 'ps'))
    for (x, p) in out_moves:
        lines.append('mov r%d.%s, r%d.%s' % (x[0], 'xyzw'[x[1]], tmap[p[0]], 'xyzw'[p[1]]))
    lines += xbody[i1:]
    text = '\n'.join(lines) + '\n'
    prog = sm3asm.parse_text(text)
    prog = dce(prog)
    return prog


def dce(prog):
    """eliminazione codice morto per componente sulle parti lineari; i blocchi if/endif restano interi (letture vive, scritture 'forse')."""
    B = body(prog); st = stypes(prog)
    depth = []; d = 0
    for i in B:
        if i.op in ('if', 'ifc'): d += 1
        depth.append(d)
        if i.op == 'endif': d -= 1
    live = set(); keep = [False] * len(B)
    for k in range(len(B) - 1, -1, -1):
        i = B[k]
        side = i.op in ('texkill', 'if', 'ifc', 'else', 'endif') or (i.ops and i.ops[0].isdst and i.ops[0].rtype != sm3asm.RT_TEMP)
        inblk = depth[k] > 0
        w = set()
        if i.ops and i.ops[0].isdst and i.ops[0].rtype == sm3asm.RT_TEMP:
            w = {(i.ops[0].num, c) for c in range(4) if i.ops[0].wm >> c & 1}
            if i.op == 'sincos': w = {(i.ops[0].num, c) for c in range(4) if i.ops[0].wm >> c & 1}
        if not side and not inblk and not (w & live): continue
        keep[k] = True
        if not inblk: live -= w
        for j, o in enumerate(i.ops):
            if o.isdst: continue
            if o.rtype == sm3asm.RT_TEMP:
                for c in lanes(i, j, st): live.add((o.num, c))
            if o.rel and o.relop is not None and o.relop.rtype == sm3asm.RT_TEMP: live |= {(o.relop.num, c) for c in range(4)}
    newB = [i for k, i in enumerate(B) if keep[k]]
    # intestazione: via dcl di sampler/ingressi e def non usati; sampler oltre s15 = errore (ps_3_0)
    used = {(o.rtype, o.num) for i in newB for o in i.ops if not o.isdst} | {(o.rtype, o.num) for i in newB for o in i.ops if o.isdst}
    H = []
    for i in header(prog):
        o = i.ops[0]
        if i.op == 'dcl' and o.rtype in (sm3asm.RT_SAMPLER, sm3asm.RT_INPUT, sm3asm.RT_MISC) and (o.rtype, o.num) not in used: continue
        if i.op == 'def' and (sm3asm.RT_CONST, o.num) not in used: continue
        H.append(i)
    bad = [o.num for i in H if i.op == 'dcl' for o in i.ops[:1] if o.rtype == sm3asm.RT_SAMPLER and o.num > 15]
    if bad: raise Fail('sampler oltre s15 ancora usati: %s' % bad)
    return sm3asm.Program(prog.kind, prog.major, prog.minor, H + newB)


# ---------------------------------------------------------------------------------------------- ricerca del donatore
class GlobalNames:
    """nome -> registro stabile nel processo (solo per confrontare blocchi Xbox fra shader diversi)."""
    def __init__(self):
        self.tab = {}; self.pool = [r for r in range(224) if not 100 <= r < 116]
    def fn(self, name, j, count):
        if name == 'MaterialParams': return 100 + j
        k = (name, j)
        if k not in self.tab:
            if not self.pool: return None
            self.tab[k] = self.pool.pop(0)
        return self.tab[k]


GN = GlobalNames()
_BLK = {}


def xblock_info(lib, xid, xslot):
    """(prog, i0, i1, ins+MP, outs) del blocco luci Xbox, tradotto con nomi globali; None se non traducibile."""
    key = (lib, xid, xslot)
    if key in _BLK: return _BLK[key]
    L = libs(); src = {'X': L['X'], 'D': L['D']}[lib][xid]
    try:
        blob = src['entries'][src['slots'][xslot]]['blob']
        prog, i0, i1, tr = translate_x(blob, GN.fn, lambda n, c: c, xbools(blob))
        if i0 is None: raise Fail('nessun blocco')
        ins, outs = live_in_out(prog, i0, i1)
        allin = list(ins) + [('c',) + m for m in sorted(mp_reads(prog, i0, i1))]
        r = (prog, i0, i1, allin, outs)
    except (xenos2sm3.Reject, Fail, Exception):
        r = None
    _BLK[key] = r
    return r


def find_donors(lib, xid, xslot, exclude_p=(), want=1, prefer=()):
    """coppie base (xs, pd) col blocco luci Xbox equivalente a quello di (lib, xid, slot xslot). Prima i 'prefer'."""
    me = xblock_info(lib, xid, xslot)
    if me is None: return []
    prog, i0, i1, ins, outs = me
    ntemp = sum(1 for i in ins if len(i) == 2); nmp = len(ins) - ntemp
    env = Env(2); found = []
    cands = [c for c in prefer] + [c for c in lit_pairs() if c not in prefer]
    for xs, pd in cands:
        if pd in exclude_p or (lib == 'X' and xs == xid): continue
        o = xblock_info('X', xs, xslot)
        if o is None: continue
        pB, b0, b1, inB, outB = o
        if len(outB) != len(outs) or sum(1 for i in inB if len(i) == 3) != nmp or abs((b1 - b0) - (i1 - i0)) > 0.05 * (i1 - i0) + 4: continue
        try:
            im, om = match_blocks(prog, i0, i1, ins, outs, pB, b0, b1, inB, outB, env)
            if verify_blocks(prog, i0, i1, ins, outs, pB, b0, b1, inB, outB, im, om, env) >= 0.99:
                found.append((xs, pd))
                if len(found) >= want: break
        except Fail:
            continue
    return found


# ---------------------------------------------------------------------------------------------- oracolo
def compare_pc(progT, progP, matp, seed=5, bools=None):
    env = Env(seed, matp)
    a = env.run(progT, body(progT), env.state0(progT), bools)
    b = env.run(progP, body(progP), env.state0(progP), bools)
    ca, ka = a[0].get((sm3asm.RT_COLOROUT, 0)), a[1]; cb, kb = b[0].get((sm3asm.RT_COLOROUT, 0)), b[1]
    if ca is None or cb is None: return 0.0
    ok = np.isclose(ca, cb, **TOL).all(axis=1) & (ka == kb) | (ka & kb)
    return float(ok.mean())


def lit_pairs():
    L = libs(); X, P = L['X'], L['P']; pos = positions(); out = []
    for x, p in sorted(x2p().items()):
        if X[x]['kind'] != 1 or 2 not in pos.get(x, set()) or p not in P: continue
        sh0 = XL.parse(X[x]['entries'][X[x]['slots'][0]]['blob'])
        if not any(LIGHT_NAMES_X.search(c['name']) for c in sh0.ctab): continue
        out.append((x, p))
    return out


def family(x):
    L = libs(); sh = XL.parse(L['X'][x]['entries'][L['X'][x]['slots'][0]]['blob'])
    return tuple(sorted(c['name'] for c in sh.ctab if LIGHT_NAMES_X.search(c['name']) or c['set'] == 0))


def one(xb, pb, pd, xs, slot=0, log=None):
    """trapianto di Xb (slot Xbox slot&1) col donatore Pd (slot PC slot) e ponte Xs; confronto con Pb (stesso slot)."""
    L = libs(); X, P = L['X'], L['P']
    xblob = X[xb]['entries'][X[xb]['slots'][slot & 1]]['blob']; xsblob = X[xs]['entries'][X[xs]['slots'][slot & 1]]['blob']
    if P[pd]['slots'][slot] == 0xffffffff or P[pb]['slots'][slot] == 0xffffffff: raise Fail('slot PC %d vuoto' % slot)
    pdblob = P[pd]['entries'][P[pd]['slots'][slot]]['blob']; pbblob = P[pb]['entries'][P[pb]['slots'][slot]]['blob']
    mb = material_pairs(xs, pd)
    if not mb: raise Fail('nessun materiale ponte per Xs %d / Pd %d' % (xs, pd))
    mt = material_pairs(xb, pb)
    if not mt: raise Fail('nessun materiale per Xb %d / Pb %d' % (xb, pb))
    pbct = pc_ctab(pbblob); xnames = {n: ri for n, rs, ri, rc in pbct if rs == 3}
    progT, info = build(xblob, pdblob, xsblob, [(m[2], m[3]) for m in mb], x_samp_names=xnames, log=log)
    progP = decode_pc(pbblob)
    res = {}
    for lab, bl in (('luci_on', ALLB), ('luci_off', {}), ('misto', {0: True, 3: True, 6: True})):
        res[lab] = compare_pc(progT, progP, mt[0][3], bools=bl)
    n_instr = len(body(progT))
    return res, n_instr, info


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'oracolo'
    if mode == 'coppia':
        xb, pb, pd = map(int, sys.argv[2:5]); rev = collections.defaultdict(list)
        for x, p in x2p().items(): rev[p].append(x)
        if pd == 0:
            d = find_donors('X', xb, 0, exclude_p=(pb,))
            if not d: print('nessun donatore equivalente'); return
            xs, pd = d[0]; print('donatore trovato: Xs %d / Pd %d' % (xs, pd))
        else: xs = rev[pd][0]
        log = []
        try: print(one(xb, pb, pd, xs, log=log))
        except Fail as e: print('FAIL', e)
        print('\n'.join(log)); return
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 30; seed = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    pairs = lit_pairs()
    random.seed(seed); sample = random.sample(pairs, min(n, len(pairs)))
    rows = []; cnt = collections.Counter()
    for xb, pb in sample:
        for kind in ('unitario', 'incrociato'):
            if kind == 'unitario': xs, pd = xb, pb
            else:
                d = find_donors('X', xb, 0, exclude_p=(pb,))
                if not d:
                    rows.append((xb, pb, kind, '-', '-', 'nessun donatore equivalente', '')); cnt[(kind, 'nessun donatore')] += 1
                    print(*rows[-1], sep='\t', flush=True); continue
                xs, pd = d[0]
            log = []
            try:
                res, ni, info = one(xb, pb, pd, xs, log=log)
                ok = min(res.values()) >= 0.99
                cnt[(kind, 'PASS' if ok else 'basso')] += 1
                rows.append((xb, pb, kind, xs, pd, 'PASS' if ok else 'basso', ' '.join('%s=%.3f' % kv for kv in res.items()) + ' istr=%d' % ni))
            except Fail as e:
                cnt[(kind, 'FAIL')] += 1; rows.append((xb, pb, kind, xs, pd, 'FAIL ' + str(e)[:120], ''))
            except Exception as e:
                cnt[(kind, 'ERR')] += 1; rows.append((xb, pb, kind, xs, pd, 'ERR ' + repr(e)[:120], ''))
            print(*rows[-1], sep='\t', flush=True)
    with open(os.path.join(HERE, 'f9_oracolo.tsv'), 'w') as f:
        f.write('xb\tpb\ttipo\txs\tpd\tesito\tdettaglio\n')
        for r in rows: f.write('\t'.join(str(c) for c in r) + '\n')
    md = ['# F9 oracolo trapianto (f9_transplant.py, %d coppie, seme %d)' % (len(sample), seed), '',
          ', '.join('%s %s: %d' % (k[0], k[1], v) for k, v in sorted(cnt.items())),
          'PASS = T coincide col PC vero (>=99%% dei campioni) con luci accese, spente e miste.', 'Dettaglio: f9_oracolo.tsv']
    open(os.path.join(HERE, 'f9_oracolo.md'), 'w').write('\n'.join(md) + '\n'); print('\n'.join(md))


if __name__ == '__main__':
    main()
