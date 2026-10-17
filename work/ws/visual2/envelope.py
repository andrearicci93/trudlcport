"""envelope.py - per lib PS surrogate: inviluppo dei MaterialParams dei materiali base PC che usano la lib (stessa lunghezza); outlier dei materiali DLC convertiti."""
import sys,struct,collections
sys.path.insert(0,'/path/to/trudlcport/tools')
import material_reslot as MR, drm_reloc as R
L=MR.libs(); PM=L['PM']
mats,msh,mx2p=MR.dlc_tables()
def params(d,r):
    n=struct.unpack_from('<I',d,0x58)[0]; rel=R.parse(r,'le'); o=dict(rel.internal).get(0x5c)
    return [struct.unpack_from('<4f',d,o+16*i) for i in range(n)]
env=collections.defaultdict(list)     # (lib,n) -> list of param vectors
for k,(d,r) in PM.items():
    t=struct.unpack_from('<4I',d,0x28); p=params(d,r)
    for s in t[1:4]:
        if s: env[(s,len(p))].append(p)
def outl(p,fam):
    res=[]
    for i,v in enumerate(p):
        for c in range(4):
            vals=[f[i][c] for f in fam]
            lo,hi=min(vals),max(vals)
            x=v[c]
            m=max(abs(lo),abs(hi),1e-6)
            if x>hi+max(0.5,0.5*abs(hi)) or x<lo-max(0.5,0.5*abs(lo)): res.append((i,c,round(x,2),(round(lo,2),round(hi,2))))
    return res
tot=collections.Counter(); byidx=collections.Counter(); rows=[]
for x,v in mats.items():
    if v['source']!='converted': continue
    d,r=v['data'],v['reloc']; t=struct.unpack_from('<4I',d,0x28); p=params(d,r)
    fams=[env[(s,len(p))] for s in t[1:4] if s and len(env.get((s,len(p)),[]))>=3]
    if not fams: tot['no family']+=1; continue
    # richest family
    fam=max(fams,key=len); o=outl(p,fam)
    tot['has outlier' if o else 'clean']+=1
    for i,c,_,_ in o: byidx[i]+=1
    if o: rows.append((x,t,len(p),len(fam),o))
print(dict(tot)); print('per indice',sorted(byidx.items()))
for r in rows[:25]: print(r[0],r[1],r[2],'famN',r[3],r[4][:6])
for x in (20268,21214,20547,23396,23397):
    print(x,[r for r in rows if r[0]==x] or 'none')
