"""Per le lane R3c (PC vive, nessun candidato Xbox vivo): valore usato oggi (lane scelta da R3c, nello spazio dl) vs valore S3 (costante = modo sui ponti)."""
import sys, struct, collections; sys.path.insert(0, '/path/to/trudlcport/work/ws/shader4'); sys.path.insert(0, '/path/to/trudlcport/work/ws/codefirst')
import f9m, mp_resolve
from mp_cands import members, val
from f12_build_all import *
FAM = {(981, 1531): ([21086, 21209, 23371, 23372], [(112, 1), (113, 2)]), (111, 225): ([21087, 23568], [(107, 1)]), (300, 356): ([21126], [(107, 3), (109, 1)])}
L = libs(); D, DM, X, P = L['D'], L['DM'], L['X'], L['P']
LN = lambda l: 'c%d.%s' % (l[0], 'xyzw'[l[1]])
def exact(mp, lane):
    if mp is None: return lane
    k = [kk for kk, v in mp.items() if v == lane]; return k[0] if k else None
for (xs, pd), (mids, lanes) in FAM.items():
    res, ties = mp_resolve.resolve(xs, pd); M = members(xs, pd, 0); bridge = material_pairs(xs, pd)
    for l in lanes:
        vals = [round(float(val(s['PP'], exact(s['pmap'], l))), 6) for s in M if exact(s['pmap'], l) is not None and val(s['PP'], exact(s['pmap'], l)) is not None]
        cnt = collections.Counter(vals); mode, nm = cnt.most_common(1)[0]
        print('(%d,%d) PC %s: valori sui %d ponti %s -> modo %g (%d/%d)' % (xs, pd, LN(l), len(vals), dict(cnt), mode, nm, len(vals)))
    for mid in mids:
        dl = struct.unpack_from('>4I', DM[mid][0], 0x28)[2]; XPm = params(f9_common._Sec(*DM[mid]), 'be')
        xblob = D[dl]['entries'][D[dl]['slots'][0]]['blob']; e = P[pd]['slots'][0]
        T, info = f9m.build(xblob, P[pd]['entries'][e]['blob'], X[xs]['entries'][X[xs]['slots'][0]]['blob'], [(m_[2], m_[3]) for m_ in bridge], log=[], x_opts={}, mp_res=res)
        imap = dict(f9m.CTX['imap']); out = {}
        for l in lanes:
            r = res[l]
            if r[0] == 'lane':
                t = imap[('c',) + tuple(r[1])]; out[LN(l)] = ('lane->', round(float(XPm[t[1] - 100][t[2]]), 6))
            else: out[LN(l)] = (r[0], r[1])
        print('   mat %d: valore usato oggi %s' % (mid, out))
