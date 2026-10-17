"""Misura: traduzione Xenos->SM3 delle coppie base in posizione 0 e 1 (passi depth/ombra) contro tutte le voci PC occupate. Decide se vale tradurre pos0/pos1."""
import sys, os, collections, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from f3_validate import *
BP = json.load(open(os.path.join(HERE, 'pc_ctab_by_pos.json')))
ALIAS = {'CameraPosition': 'g_CameraPosition', 'TimeVector': 'TimeVectorPS'}
def cfn_for(q):
    tab = BP[str(q)]
    def f(name, j, count):
        name = ALIAS.get(name, name)
        n = tab.get(name)
        if n is None: return None
        return n[0][0][0] + j
    return f
res = collections.Counter(); detail = []
pos = positions()
for q in (0, 1):
    cf = cfn_for(q)
    for x, p in sorted(x2p().items()):
        if libs()['X'][x]['kind'] != 1 or pos.get(x) != {q}: continue
        for xs in (0, 1):
            blob = libs()['X'][x]['entries'][libs()['X'][x]['slots'][xs]]['blob']
            try:
                tr = xenos2sm3.translate(blob, cf, samp=lambda n, c: c)
            except xenos2sm3.Reject as e:
                res[(q, 'REJECT:' + str(e)[:30])] += 1; continue
            prog = tr.prog
            best = 0
            for k, s in enumerate(libs()['P'][p]['slots']):
                if s == 0xffffffff: continue
                pprog = pc_prog(libs()['P'][p]['entries'][s]['blob'])
                try:
                    r = compare(prog, pprog)
                except Exception as e:
                    continue
                best = max(best, r['frac'])
            res[(q, 'best>=0.95' if best >= 0.95 else ('best>=0.5' if best >= 0.5 else 'best<0.5'))] += 1
print(sorted(res.items()))
