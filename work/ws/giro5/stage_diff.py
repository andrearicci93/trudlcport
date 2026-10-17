import sys, os, collections
sys.path.insert(0, '/path/to/trudlcport/tools')
import drm
ROOT = '/path/to/trudlcport'
A = ROOT + '/work/baseline/B87_materiali19/mods/'; S = sys.argv[1] if len(sys.argv) > 1 else ROOT + '/work/ws/giro5/stage_B88/mods/'
def secs(p): return drm.sections_with_data(drm.cdrm_decode(open(p, 'rb').read(), 'le'), 'le')[1]
for dp, _, fs in sorted(os.walk(S)):
    for f in sorted(fs):
        p = os.path.join(dp, f); rel = os.path.relpath(p, S)
        a = secs(A + rel); b = secs(p)
        ka = collections.Counter((s['type'], s['id']) for s in a); kb = collections.Counter((s['type'], s['id']) for s in b)
        added = sorted(set(kb) - set(ka)); removed = sorted(set(ka) - set(kb))
        da = {(s['type'], s['id']): s for s in a}; db = {(s['type'], s['id']): s for s in b}
        ch = []
        for k in sorted(set(da) & set(db)):
            x, y = da[k]['data'], db[k]['data']
            if x != y: ch.append((k, 'len' if len(x) != len(y) else sum(1 for i in range(len(x)) if x[i] != y[i])))
        print(rel, '| sezioni', len(a), '->', len(b), '| aggiunte', added, '| rimosse', removed, '| cambiate(type,id,byte)', ch)
