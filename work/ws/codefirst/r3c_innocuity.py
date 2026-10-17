"""Giro 3 (advisor): le lane decise da R3c sono VIVE nel PC (lane_live2.py). Un'assegnazione e' innocua per un materiale solo se i valori dei candidati nel materiale DLC
(spazio dl, via imap) coincidono. Per ogni materiale delle famiglie 981/111/300 (+ costanti solo-PC) stampa i valori dei candidati alternativi."""
import sys, struct; sys.path.insert(0, '/path/to/trudlcport/work/ws/shader4'); sys.path.insert(0, '/path/to/trudlcport/work/ws/codefirst')
import f9m, mp_resolve, struct_resolve
from f12_build_all import *
FAM = {(981, 1531): [21086, 21209, 23371, 23372], (111, 225): [21087, 23568], (300, 356): [21126]}
L = libs(); D, DM, X, P = L['D'], L['DM'], L['X'], L['P']
LN = lambda l: 'c%d.%s' % (l[0], 'xyzw'[l[1]])
for (xs, pd), mids in FAM.items():
    res, ties = mp_resolve.resolve(xs, pd); AG = mp_resolve.AGR[(xs, pd, 0)]
    bridge = material_pairs(xs, pd)
    print('=== famiglia (%d,%d): lane con candidati multipli all\'ingresso di R3c: %s' % (xs, pd, {LN(l): {LN(x): v for x, v in sc.items()} for l, sc in AG.items()}))
    for mid in mids:
        dl = struct.unpack_from('>4I', DM[mid][0], 0x28)[2]; XPm = params(f9_common._Sec(*DM[mid]), 'be')
        xblob = D[dl]['entries'][D[dl]['slots'][0]]['blob']; e = P[pd]['slots'][0]
        T, info = f9m.build(xblob, P[pd]['entries'][e]['blob'], X[xs]['entries'][X[xs]['slots'][0]]['blob'], [(m_[2], m_[3]) for m_ in bridge], log=[], x_opts={}, mp_res=res)
        imap = dict(f9m.CTX['imap'])
        for l, sc in AG.items():
            vals = {}
            for x in sc:
                t = imap.get(('c',) + tuple(x))
                vals[LN(x)] = round(float(XPm[t[1] - 100][t[2]]), 6) if t else None
            ch = res.get(l)
            inn = len({v for v in vals.values() if v is not None}) == 1
            print('  mat %d (dl %d): PC %s scelta %s | valori dei candidati nel materiale %s -> %s' % (mid, dl, LN(l), ch, vals, 'INNOCUA' if inn else 'NON INNOCUA'), flush=True)
