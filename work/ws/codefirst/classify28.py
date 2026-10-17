import sys,json,collections,re
S4='/path/to/trudlcport/work/ws/shader4'; sys.path.insert(0,S4)
from f9_common import *
V0=json.load(open('/path/to/trudlcport/work/ws/codefirst/out_regimeA/V0.json'))
fam={}
for (xs,pd) in {tuple(r['donor']) for r in V0.values() if r.get('donor')}:
    br=material_pairs(xs,pd)
    ident=sum(1 for _,_,XP,PP in br if len(XP)==len(PP) and all(abs(a-b)<1e-6 for x,p in zip(XP,PP) for a,b in zip(x,p)))
    samelen=sum(1 for _,_,XP,PP in br if len(XP)==len(PP))
    fam[(xs,pd)]=(len(br),ident,samelen)
rows=[]; cat=collections.Counter()
for mid,r in sorted(V0.items(),key=lambda kv:int(kv[0])):
    if r['status']=='costruito': continue
    why=r['why'] or ''; d=tuple(r['donor']) if r.get('donor') else None
    if r['status']=='escluso-lifetime/regime-B':
        c='B: lifetime/copie DRM' if ('assente' in why or 'diversa' in why) and 'pos2' not in why else 'B: surrogato modificato da altri fix (ragnatele, Regime B)'
    elif r['status']=='escluso-nessun-donatore': c='nessun donatore'
    else:
        f=fam.get(d); 
        if 'MaterialParams' in why or 'non rimappabile' in why or 'ingresso Pd' in why:
            c='ponte base con params PC != Xbox (layout diverso)' if f and f[1]<f[0] else 'ponte base identico ma blocco luci non equivalente'
        else: c='altro: '+why[:40]
    cat[c]+=1; rows.append((mid,c,d,fam.get(d),why[:90]))
for r in rows: print(r)
print(); 
for k,v in cat.most_common(): print(v,k)
