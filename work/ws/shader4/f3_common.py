"""Strumenti comuni F3/F4: tabelle nome->registro PC, esecuzione VM con ingressi per semantica, confronto numerico."""
import sys, os, pickle, json, struct, collections
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, 'work/ws/xenos')); sys.path.insert(0, os.path.join(ROOT, 'tools'))
import sm3asm, sm3dis, sm3vm, shaderlib, xenos2sm3
LIBS = None
def libs():
    global LIBS
    if LIBS is None: LIBS = pickle.load(open(os.path.join(ROOT, 'work/render/shaderlibs.pkl'), 'rb'))
    return LIBS
X2P = None
def x2p():
    global X2P
    if X2P is None: X2P = pickle.load(open(os.path.join(ROOT, 'work/render/shader_x2p.pkl'), 'rb'))
    return X2P

_pcn = None
def pc_names():
    """{nome float: [(reg,count),...] ordinati per frequenza}"""
    global _pcn
    if _pcn is None:
        d = json.load(open(os.path.join(HERE, 'pc_ctab_by_pos.json')))
        _pcn = {n: c for n, c in d['2'].items()}
    return _pcn

def const_fn(name, j, count):
    """registro PC dell'elemento j della costante float 'name' (None se il nome non esiste su PC)."""
    n = pc_names().get(name)
    if n is None: return None
    reg = n[0][0][0]
    return reg + j

def ctab_pc(blob):
    b = blob[:sm3dis.bytecode_len(blob)]
    return sm3dis.ctab_of(b)

def pc_prog(blob):
    return sm3asm.decode(blob[:sm3dis.bytecode_len(blob)])

def inputs_of(prog):
    """{(usage, index): set(comp)} dai dcl di un programma PS; ritorna anche mappa semantica -> registro v."""
    out = {}; vmap = {}
    for ins in prog.instrs():
        if ins.op == 'dcl' and ins.ops[0].rtype == sm3asm.RT_MISC:
            m = ins.ops[0].wm
            out[('misc', ins.ops[0].num)] = set(c for c in range(4) if m >> c & 1); continue
        if ins.op == 'dcl' and ins.ops[0].rtype == sm3asm.RT_INPUT:
            u = ins.usage & 31; ix = (ins.usage >> 16) & 15
            m = ins.ops[0].wm
            out[(u, ix)] = set(c for c in range(4) if m >> c & 1)
            vmap[(u, ix)] = ins.ops[0].num
    return out, vmap

def compare(progA, progB, N=1000, seed=7, tol=1e-3, atol=2e-4, cvals=None, cvalsB=None):
    """Esegue due programmi PS sugli stessi ingressi (per semantica), stesse costanti (per registro PC) e stessa funzione di texture
    (per registro sampler). Ritorna dict con frazione campioni ok."""
    rng = np.random.RandomState(seed)
    inA, vA = inputs_of(progA); inB, vB = inputs_of(progB)
    sem = sorted(set(inA) | set(inB), key=str)
    vals = {s: rng.uniform(0.0, 1.0, (N, 4)).astype(np.float32) for s in sem}
    vpos = rng.uniform(0, 1500, (N, 4)).astype(np.float32); vpos[:, 2:] = 0
    vface = np.repeat(np.where(rng.rand(N, 1) < 0.5, -1.0, 1.0).astype(np.float32), 4, axis=1)
    def mk(vmap):
        d = {(sm3asm.RT_INPUT, vmap[s]): vals[s] for s in vmap if s[0] != 'misc'}
        d[(sm3asm.RT_MISC, 0)] = vpos
        d[(sm3asm.RT_MISC, 1)] = vface
        return d
    consts = {r: rng.uniform(0.05, 1.5, 4).astype(np.float32) for r in range(224)}
    if cvals: consts.update(cvals)
    tex = sm3vm.det_tex(lambda s: s)
    constsB = dict(consts)
    if cvalsB: constsB.update(cvalsB)
    oa = sm3vm.run(progA, mk(vA), consts, tex, N)
    ob = sm3vm.run(progB, mk(vB), constsB, tex, N)
    ra = oa.get('oC0', np.zeros((N, 4), np.float32)); rb = ob.get('oC0', np.zeros((N, 4), np.float32))
    ka, kb = oa['kill'], ob['kill']
    # per i campioni uccisi in entrambi il colore non conta
    both = ka & kb
    err = np.abs(ra - rb) <= tol * np.maximum(np.abs(ra), np.abs(rb)) + atol
    ok = np.all(err, axis=1) & (ka == kb) | both
    return dict(frac=float(ok.mean()), kill_mismatch=float((ka != kb).mean()), usedA=oa['used_consts'], usedB=ob['used_consts'],
                sampA=oa['used_samplers'], sampB=ob['used_samplers'], maxerr=float(np.nanmax(np.abs(ra - rb))))
