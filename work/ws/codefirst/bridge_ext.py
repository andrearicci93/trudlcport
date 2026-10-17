"""Ponti estesi (Task 3): per la famiglia (xs, pd) raccoglie i materiali base delle coppie (xs', pd') con
  (a) blocco luci Xbox di xs' equivalente a quello di xs (match_blocks verificato >= 0.99)  -> mappa lane Xbox xs' -> xs
  (b) blocco luci PC di pd' equivalente a quello di pd (match_blocks verificato >= 0.99)    -> mappa lane PC pd' -> pd
e li riporta nello spazio di lane (xs, pd) come matrici 16x4 con NaN dove la lane non e' definita. Sola lettura.
Regola: se i blocchi sono equivalenti su entrambi i lati la relazione di layout MaterialParams e' la stessa della famiglia, quindi
i valori dei loro materiali sono campioni aggiuntivi della STESSA relazione (intersezione dei candidati per valore)."""
import sys, collections
S4 = '/path/to/trudlcport/work/ws/shader4'; sys.path.insert(0, S4)
import numpy as np
from f9_transplant import *
import f9_common


def pc_block_info(pd, slot=0):
    L = libs(); P = L['P']
    blob = P[pd]['entries'][P[pd]['slots'][slot]]['blob']
    prog = decode_pc(blob); p0, p1 = pc_light_block(prog)
    if p0 is None: return None
    ins, outs = live_in_out(prog, p0, p1)
    allin = list(ins) + [('c',) + m for m in sorted(mp_reads(prog, p0, p1))]
    return prog, p0, p1, allin, outs


_cache = {}


def extra_bridges(xs, pd, slot=0, log=None):
    key = (xs, pd, slot)
    if key in _cache: return _cache[key]
    log = log if log is not None else []
    out = []
    me = xblock_info('X', xs, slot); pme = pc_block_info(pd, slot)
    if me is None or pme is None: _cache[key] = out; return out
    prog, i0, i1, ins, outs = me
    pprog, q0, q1, pins, pouts = pme
    env = Env(2)
    for (x2, p2) in find_donors('X', xs, slot, want=60):
        if (x2, p2) == (xs, pd): continue
        o = xblock_info('X', x2, slot)
        if o is None: continue
        pB, b0, b1, inB, outB = o
        try:
            imx, _ = match_blocks(prog, i0, i1, ins, outs, pB, b0, b1, inB, outB, env)
        except Fail as e:
            log.append('(%d,%d) Xbox: %s' % (x2, p2, e)); continue
        ppB = pc_block_info(p2, slot)
        if ppB is None: log.append('(%d,%d) PC: nessun blocco' % (x2, p2)); continue
        qprog, c0, c1, qins, qouts = ppB
        try:
            imp, _ = match_blocks(pprog, q0, q1, pins, pouts, qprog, c0, c1, qins, qouts, env)
        except Fail as e:
            log.append('(%d,%d) PC non equivalente: %s' % (x2, p2, str(e)[:80])); continue
        mpx = {k: v for k, v in imx.items() if len(k) == 3}      # lane Xbox x2 (r,c) -> lane xs
        mpp = {k: v for k, v in imp.items() if len(k) == 3}      # lane PC p2 -> lane pd
        for mx, mp, XP, PP in material_pairs(x2, p2):
            XPc = np.full((16, 4), np.nan); PPc = np.full((16, 4), np.nan)
            for (_, r, c), (_, r0, c0_) in mpx.items():
                if r - 100 < len(XP): XPc[r0 - 100][c0_] = XP[r - 100][c]
            for (_, r, c), (_, r0, c0_) in mpp.items():
                if r - 100 < len(PP): PPc[r0 - 100][c0_] = PP[r - 100][c]
            out.append((XPc, PPc, (x2, p2, mx, mp)))
        log.append('(%d,%d): Xbox lane mappate %d, PC lane mappate %d, materiali %d' % (x2, p2, len(mpx), len(mpp), len(material_pairs(x2, p2))))
    _cache[key] = out
    return out


if __name__ == '__main__':
    for xs, pd in ((981, 1531), (111, 225), (300, 356), (164, 207), (1409, 1038), (1431, 1060)):
        lg = []; ex = extra_bridges(xs, pd, log=lg)
        print('=== (%d,%d): %d ponti estesi' % (xs, pd, len(ex)))
        for l in lg: print('   ', l)
