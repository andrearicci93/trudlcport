"""sm3opt.py - ottimizzazioni sicure su programmi SM3 senza flusso di controllo (output del traduttore): eliminazione codice morto
per componente, dcl minimi, def inutilizzati. Un `texkill` e' sempre un effetto collaterale (mai eliminato)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sm3asm import *

NARROW = {'mov', 'add', 'sub', 'mul', 'mad', 'min', 'max', 'slt', 'sge', 'cmp', 'lrp', 'frc', 'abs', 'sgn', 'dp3', 'dp4', 'dp2add',
          'rcp', 'rsq', 'exp', 'log', 'pow', 'nrm'}
SCALAR_IN = {'rcp', 'rsq', 'exp', 'log', 'sincos'}


def lanes_read(ins, k, dstmask, sampler_type=None):
    """Componenti (swizzlate) lette dalla sorgente k di ins -> lista di indici componente del registro sorgente."""
    o = ins.ops[k]
    sw = [(o.swz >> (2 * l)) & 3 for l in range(4)]
    op = ins.op
    if op in ('dp3', 'nrm', 'crs'): lanes = [0, 1, 2] if op != 'nrm' else [0, 1, 2]
    elif op == 'dp4': lanes = [0, 1, 2, 3]
    elif op == 'dp2add': lanes = [0] if k == 3 else [0, 1]
    elif op in SCALAR_IN: lanes = [0]
    elif op == 'pow': lanes = [0]
    elif op in ('texld', 'texldl', 'texldd') and k == 1:
        t = sampler_type
        lanes = [0, 1] if t == 2 else [0, 1, 2]
        if ins.op == 'texldl' or ins.ctrl in (1, 2): lanes = [0, 1, 2, 3]
    elif op in ('lit', 'dst', 'dsx', 'dsy', 'lrp') and False: lanes = [0, 1, 2, 3]
    elif op == 'texkill': lanes = [0, 1, 2]
    else:
        lanes = [l for l in range(4) if dstmask >> l & 1]
    return sorted(set(sw[l] for l in lanes)), lanes


def analyse(prog):
    stype = {}
    for ins in prog.items:
        if isinstance(ins, Instr) and ins.op == 'dcl' and ins.ops[0].rtype == RT_SAMPLER:
            stype[ins.ops[0].num] = (ins.usage >> 27) & 15
    return stype


def rw(ins, stype):
    """(reads:set((rtype,num,comp)), writes:set(...)) di una istruzione ALU/tex."""
    reads, writes = set(), set()
    if ins.op in ('dcl', 'def', 'defi', 'defb'): return reads, writes
    ops = ins.ops
    if ins.op == 'texkill':
        o = ops[0]
        for c in (0, 1, 2): reads.add((o.rtype, o.num, c))
        return reads, writes
    d = ops[0]
    mask = d.wm
    for l in range(4):
        if mask >> l & 1: writes.add((d.rtype, d.num, l))
    for k in range(1, len(ops)):
        o = ops[k]
        if o.rtype == RT_SAMPLER: continue
        stp = stype.get(ops[2].num) if ins.op.startswith('texld') and len(ops) > 2 else None
        comps, _ = lanes_read(ins, k, mask, stp)
        for c in comps: reads.add((o.rtype, o.num, c))
        if o.rel: raise ValueError('rel non supportato')
    return reads, writes


def dce(prog):
    stype = analyse(prog)
    items = prog.items
    live = set()
    for c in range(4):
        for n in range(4): live.add((RT_COLOROUT, n, c))
        live.add((RT_DEPTHOUT, 0, c))
    keep = [False] * len(items)
    for i in range(len(items) - 1, -1, -1):
        ins = items[i]
        if not isinstance(ins, Instr): keep[i] = True; continue
        if ins.op in ('dcl', 'def', 'defi', 'defb'): keep[i] = True; continue
        reads, writes = rw(ins, stype)
        if ins.op == 'texkill':
            keep[i] = True; live |= reads; continue
        if ins.pred: raise ValueError('predicazione non supportata in dce')
        if writes & live:
            keep[i] = True
            if ins.op in NARROW:
                d = ins.ops[0]
                m = sum(1 << c for (_, _, c) in writes if (d.rtype, d.num, c) in live)
                if m != d.wm:
                    d.wm = m
                    reads, writes = rw(ins, stype)
            live -= writes
            live |= reads
    prog.items = [it for it, k in zip(items, keep) if k]
    return prog


def prune_decls(prog):
    """Dopo dce: restringe i dcl di input alle componenti realmente lette, elimina dcl/def inutilizzati."""
    stype = analyse(prog)
    used_in = {}      # (rtype,num) -> comps lette
    used_c = set(); used_s = set()
    for ins in prog.items:
        if not isinstance(ins, Instr) or ins.op in ('dcl', 'def', 'defi', 'defb'): continue
        reads, _ = rw(ins, stype)
        for t, n, c in reads:
            if t in (RT_INPUT, RT_MISC): used_in.setdefault((t, n), set()).add(c)
            if t in (RT_CONST, RT_CONST2): used_c.add(n + (2048 if t == RT_CONST2 else 0))
        for o in ins.ops:
            if o.rtype == RT_SAMPLER: used_s.add(o.num)
    out = []
    for it in prog.items:
        if isinstance(it, Instr):
            if it.op == 'dcl':
                o = it.ops[0]
                if o.rtype in (RT_INPUT, RT_MISC):
                    u = used_in.get((o.rtype, o.num))
                    if not u: continue
                    if o.rtype == RT_MISC and o.num == 1: out.append(it); continue     # vFace: scalare
                    o.wm = sum(1 << c for c in u if o.wm >> c & 1) or o.wm
                elif o.rtype == RT_SAMPLER and o.num not in used_s: continue
            elif it.op == 'def':
                if it.ops[0].num not in used_c: continue
        out.append(it)
    prog.items = out
    return prog


def optimize(prog):
    dce(prog)
    prune_decls(prog)
    return prog
