"""Candidati per lane: per ogni lane MaterialParams letta dal blocco PC del donatore pd, le lane Xbox (spazio xs) compatibili con TUTTI i campioni
(ponte reale + ponti estesi) tenendo conto delle SIMMETRIE dei blocchi (lane scambiabili senza cambiare la funzione). Sola lettura."""
import sys, collections, itertools
S4 = '/path/to/trudlcport/work/ws/shader4'; sys.path.insert(0, S4); sys.path.insert(0, '/path/to/trudlcport/work/ws/codefirst')
import numpy as np
from f9_transplant import *
from match_all import match_all, verify_b
import bridge_ext


def swap_classes(pA, a0, a1, inA, outA, pB, b0, b1, inB, outB, env, im, om, bools=None):
    """lane MP di B scambiabili (swap dei target in im verificato >= 0.99) -> classi (union-find)."""
    mpB = [k for k in inB if len(k) == 3]; par = {k: k for k in mpB}
    def f(k):
        while par[k] != k: par[k] = par[par[k]]; k = par[k]
        return k
    alt = {(k[1], k[2]): {(k[1], k[2])} for k in mpB}
    for i in range(len(mpB)):
        for j in range(i + 1, len(mpB)):
            k1, k2 = mpB[i], mpB[j]
            if k1 not in im or k2 not in im: continue
            im2 = dict(im); im2[k1], im2[k2] = im[k2], im[k1]
            if verify_b(pA, a0, a1, inA, outA, pB, b0, b1, inB, outB, im2, om, env, bools) >= 0.99:
                alt[(k1[1], k1[2])].add((k2[1], k2[2])); alt[(k2[1], k2[2])].add((k1[1], k1[2]))
    return alt


def sym_self(prog, i0, i1, ins, outs, env, bools=None):
    """simmetrie del blocco con se' stesso: lane MP scambiabili (identita' + trasposizioni)."""
    mp = [k for k in ins if len(k) == 3]
    im = {k: k for k in ins}; om = {o: o for o in outs}
    return swap_classes(prog, i0, i1, ins, outs, prog, i0, i1, ins, outs, env, im, om, bools)


def members(xs, pd, slot=0):
    """lista di campioni: dict(XP, PP, xmap: lane_member->lane_canonica Xbox, xcls, pmap, pcls)."""
    env = Env(2); res = []
    A = xblock_info('X', xs, slot); PA = bridge_ext.pc_block_info(pd, slot)
    pA, a0, a1, inA, outA = A; qA, q0, q1, qinA, qoutA = PA
    # il ponte reale: mappa identita', simmetrie del blocco con se' stesso
    sx = sym_self(pA, a0, a1, inA, outA, env); sp = sym_self(qA, q0, q1, qinA, qoutA, env, ALLB)
    for mx, mp, XP, PP in material_pairs(xs, pd):
        res.append(dict(tag=('reale', xs, pd, mx), XP=XP, PP=PP, xmap=None, pmap=None, xcls=sx, pcls=sp))
    for (x2, p2) in find_donors('X', xs, slot, want=60):
        if (x2, p2) == (xs, pd): continue
        B = xblock_info('X', x2, slot); PB = bridge_ext.pc_block_info(p2, slot)
        if B is None or PB is None: continue
        pB, b0, b1, inB, outB = B; qB, c0, c1, qinB, qoutB = PB
        try:
            imx, omx = match_blocks(pA, a0, a1, inA, outA, pB, b0, b1, inB, outB, env)
            sol = match_all(qA, q0, q1, qinA, qoutA, qB, c0, c1, qinB, qoutB, env, cap=1, bools=ALLB)
            if not sol: continue
            imp, omp = sol[0]
        except Fail: continue
        xc = swap_classes(pA, a0, a1, inA, outA, pB, b0, b1, inB, outB, env, imx, omx)
        pc = swap_classes(qA, q0, q1, qinA, qoutA, qB, c0, c1, qinB, qoutB, env, imp, omp, ALLB)
        xm = {(k[1], k[2]): (v[1], v[2]) for k, v in imx.items() if len(k) == 3}
        pm = {(k[1], k[2]): (v[1], v[2]) for k, v in imp.items() if len(k) == 3}
        for mx, mp, XP, PP in material_pairs(x2, p2):
            res.append(dict(tag=('ext', x2, p2, mx), XP=XP, PP=PP, xmap=xm, pmap=pm, xcls=xc, pcls=pc))
    return res


def inv_alt(mp, cls, lane):
    """lane canonica -> insieme delle lane del membro che possono rappresentarla (classi di simmetria incluse)."""
    if mp is None: return set(cls.get(lane, {lane})) | {lane}
    srcs = [k for k, v in mp.items() if v == lane]
    out = set()
    for s in srcs: out |= cls.get(s, {s}) | {s}
    return out


def val(M, lane):
    r, c = lane
    return M[r - 100][c] if 0 <= r - 100 < len(M) else None


def candidates(xs, pd, slot=0):
    PA = bridge_ext.pc_block_info(pd, slot); A = xblock_info('X', xs, slot)
    mpd = sorted((k[1], k[2]) for k in PA[3] if len(k) == 3); ms = sorted((k[1], k[2]) for k in A[3] if len(k) == 3)
    M = members(xs, pd, slot); out = {}
    for l in mpd:
        cs = []
        for x in ms:
            ok = True; n = 0
            for s in M:
                Ls = inv_alt(s['pmap'], s['pcls'], l); Xs_ = inv_alt(s['xmap'], s['xcls'], x)
                hit = any((val(s['PP'], a) is not None and val(s['XP'], b) is not None and abs(val(s['PP'], a) - val(s['XP'], b)) < 1e-6) for a in Ls for b in Xs_)
                n += 1
                if not hit: ok = False; break
            if ok: cs.append(x)
        out[l] = cs
    return mpd, ms, out, len(M)


if __name__ == '__main__':
    xs, pd = int(sys.argv[1]), int(sys.argv[2])
    mpd, ms, out, n = candidates(xs, pd)
    print('=== (%d,%d): %d campioni; lane PC lette %d; lane Xbox lette %d' % (xs, pd, n, len(mpd), len(ms)))
    for l in mpd: print('  PC c%d.%s <- Xbox %s' % (l[0], 'xyzw'[l[1]], ['c%d.%s' % (x[0], 'xyzw'[x[1]]) for x in out[l]]))
