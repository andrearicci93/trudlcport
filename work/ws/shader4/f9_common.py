"""F9 - strumenti comuni del trapianto: traduzione Xbox senza ottimizzazione con blocco luci delimitato, analisi ingressi/uscite di un
intervallo di istruzioni SM3, esecuzione parziale con stato iniettato."""
import sys, os, re, collections, itertools
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from f3_validate import *
import sm3opt
import xenos_xlat as XL
from f5_census_lit import bool_names

LIGHT_BOOL_X = 'LightEnabled'
LIGHT_NAMES_X = re.compile(r'p_Lights|ParallelShadow|ShadowMap|p_ShadowEnabled|p_ProjectionEnabled|LightEnabled')
LIGHT_PC = re.compile(r'SunLight|ShadowLight|NonShadowLight|WorldToShadowMap|ShadowDepthBias|ShadowMapSampler|LightEnabled|ModulationMap')
SKIP = ('dcl', 'def', 'defi', 'defb')


def body(prog):
    return [i for i in prog.instrs() if i.op not in SKIP]


def header(prog):
    return [i for i in prog.instrs() if i.op in SKIP]


def sub_program(prog, instrs):
    """Programma con le dichiarazioni/def di prog e le istruzioni date."""
    return sm3asm.Program(prog.kind, prog.major, prog.minor, header(prog) + list(instrs))


def xbox_light_block(tr):
    """(k0, k1) CF del blocco luci: primo cond_jmp su un bool LightEnabled -> sua destinazione. None se assente."""
    return tr.light_cf


def translate_x(blob, cfn, samp, bools_by_name, opts=None):
    """Traduce senza ottimizzazione e ritorna (prog, i0, i1): i0/i1 = indici in body(prog) del blocco luci [i0, i1) o None."""
    sh = XL.parse(blob); bn = bool_names(sh)
    bools = {i: bools_by_name.get(n, 0) for i, n in bn.items()}
    o = dict(opts or {}); o['noopt'] = True
    tr = xenos2sm3.translate(blob, cfn, bools=bools, samp=samp, opts=o)
    prog = sm3asm.parse_text(tr.text)
    nhead = len(header(prog))
    # CF del blocco: cond_jmp il cui bool e' un elemento di LightEnabled
    jmps = [r for r in tr.cfs if r['op'] == 11 and not r.get('pred') and bn.get(r.get('bool')) == LIGHT_BOOL_X]
    if not jmps: return prog, None, None, tr
    k0 = min(r['k'] for r in jmps); k1 = max(r['addr'] for r in jmps)
    def line_of(k):
        ks = [kk for kk in tr.cf_mark if kk >= k]
        return tr.cf_mark[min(ks)] if ks else tr.nout
    # indici nel body: out_start conta le istruzioni prima di self.out (dcl/def/prologo); body esclude dcl/def
    first_body = tr.out_start - nhead
    i0 = first_body + line_of(k0); i1 = first_body + line_of(k1)
    return prog, i0, i1, tr


def lanes(i, j, stype):
    dm = i.ops[0].wm if i.ops and i.ops[0].isdst else 15
    st = stype.get(i.ops[2].num) if i.op.startswith('texld') and len(i.ops) > 2 else None
    try: return sm3opt.lanes_read(i, j, dm, st)[0]
    except Exception: return [0, 1, 2, 3]


def stypes(prog):
    return {i.ops[0].num: (i.usage >> 27) & 15 for i in prog.instrs() if i.op == 'dcl' and i.ops[0].rtype == sm3asm.RT_SAMPLER}


def live_in_out(prog, i0, i1):
    """Ingressi (temp letti in [i0,i1) prima di essere scritti li') e uscite (scritti in [i0,i1) e letti dopo prima di riscrittura)."""
    B = body(prog); st = stypes(prog)
    written = set(); ins = set()
    for i in B[i0:i1]:
        for j, o in enumerate(i.ops):
            if o.isdst or o.rtype != sm3asm.RT_TEMP: continue
            for c in lanes(i, j, st):
                if (o.num, c) not in written: ins.add((o.num, c))
        if i.ops and i.ops[0].isdst and i.ops[0].rtype == sm3asm.RT_TEMP and i.op not in ('if', 'ifc'):
            for c in range(4):
                if i.ops[0].wm >> c & 1: written.add((i.ops[0].num, c))
    outs = set(); killed = set()
    for i in B[i1:]:
        for j, o in enumerate(i.ops):
            if o.isdst or o.rtype != sm3asm.RT_TEMP: continue
            for c in lanes(i, j, st):
                if (o.num, c) in written and (o.num, c) not in killed: outs.add((o.num, c))
        if i.ops and i.ops[0].isdst and i.ops[0].rtype == sm3asm.RT_TEMP:
            for c in range(4):
                if i.ops[0].wm >> c & 1: killed.add((i.ops[0].num, c))
    return sorted(ins), sorted(outs)


def pc_light_block(prog):
    """[i0, i1) della catena `if bN` di primo livello nel body di un PS PC; None se assente."""
    B = body(prog); depth = 0; start = end = None
    for k, i in enumerate(B):
        if i.op in ('if', 'ifc'):
            if depth == 0 and i.op == 'if' and i.ops and i.ops[0].rtype == sm3asm.RT_CONSTBOOL and start is None: start = k
            depth += 1
        elif i.op == 'endif':
            depth -= 1
            if depth == 0 and start is not None: end = k
    return (start, end + 1) if start is not None else (None, None)


def run_state(prog, instrs, state, consts, tex, N, bools=None):
    """Esegue le istruzioni date partendo dai registri in state ({(rtype,num): (N,4)}); ritorna i registri finali."""
    vm = sm3vm.VM(sub_program(prog, instrs), N, {k: v.copy() for k, v in state.items()}, consts, tex, bools)
    vm.exec()
    return vm.reg, vm.kill


# ---------------------------------------------------------------------------------------------- ponte Xbox <-> PC (gioco base)
import pickle, struct
from f4_build import params as _params
_MX2P = None


class _Sec:
    def __init__(self, d, r): self.data, self.reloc = d, r


def material_pairs(xlib, plib):
    """Materiali base con lib Xbox xlib in pos2 e gemello PC con plib in pos2 -> [(mid_x, mid_p, XP, PP)]."""
    global _MX2P
    if _MX2P is None: _MX2P = pickle.load(open(os.path.join(ROOT, 'work/render/material_x2p.pkl'), 'rb'))
    L = libs(); XM, PM = L['XM'], L['PM']; out = []
    for mid, (d, r) in XM.items():
        if struct.unpack_from('>4I', d, 0x28)[2] != xlib: continue
        mp = _MX2P.get(mid)
        if mp not in PM: continue
        pd, pr = PM[mp]
        if struct.unpack_from('<4I', pd, 0x28)[2] != plib: continue
        try: out.append((mid, mp, _params(_Sec(d, r), 'be'), _params(_Sec(pd, pr), 'le')))
        except Exception: continue
    return out


def pc_ctab(blob):
    bc = blob[:sm3dis.bytecode_len(blob)]
    return sm3dis.ctab_of(bc) or []


def semantic_inputs(prog, vals):
    """stato iniziale: v-registri di prog riempiti per semantica da vals {(usage,idx): (N,4)}"""
    ins, vmap = inputs_of(prog)
    return {(sm3asm.RT_INPUT, vmap[s]): vals[s] for s in vmap if s[0] != 'misc'}
