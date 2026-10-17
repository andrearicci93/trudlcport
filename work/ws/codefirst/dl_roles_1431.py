"""Giro 3 / advisor: i ruoli (esponente, bias, scala) valgono anche nel blocco luci DELLA LIB DLC realmente usata (dl), non solo nella lib ponte Xs=1431?
Per ogni materiale (1431,1060): build f9m con la regola finale -> imap (lane Xs -> lane dl), firma di contesto della lane in dl vs in Xs, valore del materiale
sulla lane dl-mappata (spazio dl, e' quello che i pareggi del Giro 2 stampavano). Uso: dl_roles_1431.py"""
import sys, struct, collections
sys.path.insert(0, '/path/to/trudlcport/work/ws/shader4'); sys.path.insert(0, '/path/to/trudlcport/work/ws/codefirst')
import f9m, mp_resolve, struct_resolve, sym_ast as SA
from f12_build_all import *
from xp_local import contexts
from xp_roles import analyse
MATS = (20344, 21093, 21258, 22596, 22597, 23186, 23437, 24043)
xs, pd = 1431, 1060
L = libs(); D, DM, X, P = L['D'], L['DM'], L['X'], L['P']
res, ties = mp_resolve.resolve(xs, pd); res0 = dict(res); ties0 = dict(ties)
res, ties, notes = struct_resolve.apply(xs, pd, res, ties)
nm = lambda r, c: 'M'
C, _r, _t, (DXs, exs, lxs, RXs), (DP, ep, lp, RP) = analyse(xs, pd, 3)
rxs = [exs[o] for o in C['sout'] if o in exs]
CXs = contexts(DXs, rxs, nm, 1, 2)
sig = lambda CC, lane: CC[lane].most_common(1)[0][0] if lane in CC else None
bridge = material_pairs(xs, pd)
dls = {}
for mid in MATS: dls.setdefault(struct.unpack_from('>4I', DM[mid][0], 0x28)[2], []).append(mid)
LN = lambda l: 'c%d.%s' % (l[0], 'xyzw'[l[1]])
print('lib DLC distinte per gli 8 materiali:', {dl: m for dl, m in dls.items()})
cand_lanes = [(109, 0), (109, 1), (107, 0), (107, 1), (107, 2), (107, 3), (100, 3)]
for dl, mids in sorted(dls.items()):
    for k in (0, 1):
        xblob = D[dl]['entries'][D[dl]['slots'][k & 1]]['blob']
        e = P[pd]['slots'][k]
        if e == 0xffffffff: continue
        T, info = f9m.build(xblob, P[pd]['entries'][e]['blob'], X[xs]['entries'][X[xs]['slots'][k & 1]]['blob'], [(m_[2], m_[3]) for m_ in bridge], log=[], x_opts={}, mp_res=res)
        CT = dict(f9m.CTX); DX, ex, lx = SA.build(CT['xprog'], CT['x0'], CT['x1'])
        rdl = [ex[o] for o in CT['xout_dl'] if o in ex]; CDL = contexts(DX, rdl, nm, 1, 2); imap = CT['imap']
        print('\n=== dl %d (materiali %s) slot %d  [uscite dl %d]' % (dl, mids, k, len(rdl)))
        for lane in cand_lanes:
            t = imap.get(('c',) + lane)
            if t is None: print('  Xs %s: nessun corrispondente in dl' % LN(lane)); continue
            tl = (t[1], t[2]); s_xs, s_dl = sig(CXs, lane), sig(CDL, tl)
            vals = {mid: round(float(params(f9_common._Sec(*DM[mid]), 'be')[tl[0] - 100][tl[1]]), 5) for mid in mids}
            print('  Xs %s -> dl %s | firma Xs==dl: %-5s | %s | valori %s' % (LN(lane), LN(tl), s_xs == s_dl, (s_dl or 'NON RAGGIUNGE LE USCITE')[:90], vals))
        print('  mp_remap PC->dl:', {LN(l): (('const %g' % v[1]) if v[0] == 'k' else LN(v)) for l, v in sorted(info['mp_remap'].items()) if l in ((107, 1), (108, 0), (108, 2), (109, 0), (109, 3))})
