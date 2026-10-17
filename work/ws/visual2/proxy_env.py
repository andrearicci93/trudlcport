"""proxy: gli outlier (rispetto all'inviluppo dei materiali base PC con la stessa lib) calano dopo la mappa di ruolo?"""
import sys,struct,collections
sys.path.insert(0,'/path/to/trudlcport/work/ws/visual2'); sys.path.insert(0,'/path/to/trudlcport/tools')
import rolefix as RF, material_reslot as MR, drm_reloc as R
L=MR.libs(); PM=L['PM']
def params(d,r):
    n=struct.unpack_from('<I',d,0x58)[0]; rel=R.parse(r,'le'); o=dict(rel.internal).get(0x5c)
    return [struct.unpack_from('<4f',d,o+16*i) for i in range(n)]
env=collections.defaultdict(list)
for k,(d,r) in PM.items():
    t=struct.unpack_from('<4I',d,0x28); p=params(d,r)
    for s in t[1:4]:
        if s: env[(s,len(p))].append(p)
def outl(p,fam):
    res=0
    for i,v in enumerate(p):
        for c in range(4):
            vals=[f[i][c] for f in fam]; lo,hi=min(vals),max(vals); x=v[c]
            if x>hi+max(0.5,0.5*abs(hi)) or x<lo-max(0.5,0.5*abs(lo)): res+=1
    return res
RF.init(); tb=ta=0; rows=[]
for xmid,m in sorted(RF.MATS.items()):
    if m['source']!='converted' or xmid==21118: continue
    r=RF.new_params(xmid)
    if r is None: continue
    cur,base,new,rule=r
    if base==new: continue
    t=struct.unpack_from('<4I',m['data'],0x28); n=len(base)
    fams=[env[(s,n)] for s in t[1:4] if s and len(env.get((s,n),[]))>=3]
    if not fams: rows.append((xmid,'nofam')); continue
    fam=max(fams,key=len); a,b=outl(base,fam),outl(new,fam); tb+=a; ta+=b; rows.append((xmid,a,b))
print('outlier totali prima',tb,'dopo',ta)
better=sum(1 for r in rows if r[1]!='nofam' and r[2]<r[1]); worse=sum(1 for r in rows if r[1]!='nofam' and r[2]>r[1]); same=sum(1 for r in rows if r[1]!='nofam' and r[2]==r[1])
print('materiali: migliorati',better,'peggiorati',worse,'uguali',same,'senza famiglia',sum(1 for r in rows if r[1]=='nofam'))
print([r for r in rows if r[0] in (20268,21214,20547,23396,23397)])
print('--- outlier residui per S comp dopo mappa (materiali con famiglia)')
cnt=collections.Counter(); unm=collections.Counter()
for xmid,m in sorted(RF.MATS.items()):
    if m['source']!='converted' or xmid==21118: continue
    r=RF.new_params(xmid)
    if r is None: continue
    cur,base,new,rule=r
    if base==new: continue
    t=struct.unpack_from('<4I',m['data'],0x28); n=len(base)
    fams=[env[(s,n)] for s in t[1:4] if s and len(env.get((s,n),[]))>=3]
    if not fams: continue
    fam=max(fams,key=len); p=RF.plan(xmid)
    for i,v in enumerate(new):
        for c in range(4):
            vals=[f[i][c] for f in fam]; lo,hi=min(vals),max(vals); x=v[c]
            if x>hi+max(0.5,0.5*abs(hi)) or x<lo-max(0.5,0.5*abs(lo)):
                cnt[(i,c)]+=1; unm[(i,c) in p['map']]+=1
print('outlier residui: su comp mappate',unm[True],'su non mappate',unm[False])
print('peggiorati:',[r for r in rows if r[1]!='nofam' and r[2]>r[1]])
for r in rows:
    if r[1]!='nofam' and r[2]>r[1]:
        xmid=r[0]; rr=RF.new_params(xmid); cur,base,new,rule=rr; p=RF.plan(xmid)
        print(xmid,p['passes'])
        for i,(a,b) in enumerate(zip(base,new)):
            if a!=b: print('  reg',i,[round(x,2) for x in a],'->',[round(x,2) for x in b])
