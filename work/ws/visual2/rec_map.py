"""rec_map.py - per record dei materiali (liste input, array 0x64/0x6c, texture entries): classe di permutazione Xbox->PC per parola sulle coppie base, poi controllo DLC convertiti."""
import sys,struct,collections
sys.path.insert(0,'/path/to/trudlcport/tools')
import material_reslot as MR, drm_reloc as R, dtp_audit as DA
L=MR.libs(); XM,PM,DM=L['XM'],L['PM'],L['DM']
mats,msh,mx2p=MR.dlc_tables()
def regions(d,rel,e):
    """yield (kind, index, k(word), offset)"""
    ptr=dict(rel.internal); out=[]
    for pi,po in enumerate((0x08,0x0c,0x10)):
        T=ptr.get(po)
        if T is None: continue
        n=struct.unpack_from(e+'I',d,T+8)[0]
        for k in range(min(n,200)):
            for w in range(7): out.append(('list%d'%pi,k,w,T+16+28*k+4*w))
    for nm,(co,po,sz) in (('a64',(0x60,0x64,16)),('a6c',(0x68,0x6c,16))):
        T=ptr.get(po); n=struct.unpack_from(e+'I',d,co)[0]
        if T is None: continue
        for k in range(min(n,200)):
            for w in range(sz//4): out.append((nm,k,w,T+sz*k+4*w))
    T=ptr.get(0x54)
    if T is not None:
        for k,(o,tid,ty,sl) in enumerate(MR.tex_entries(d,rel,e)):
            for w in range(4): out.append(('tex',k,w,o+4*w))
    return out
def key(kind,k,w,d,e): return (kind,w)
stat=collections.defaultdict(lambda:[0,DA.ALL,collections.Counter()])
vals=collections.defaultdict(collections.Counter)
n=0
for xid,(xd,xr) in XM.items():
    p=mx2p.get(xid)
    if p not in PM: continue
    pd,pr=PM[p]; xrel=R.parse(xr,'be'); prel=R.parse(pr,'le')
    rx=regions(xd,xrel,'>'); rp=regions(pd,prel,'<')
    if [(a,b,c) for a,b,c,_ in rx]!=[(a,b,c) for a,b,c,_ in rp]: continue
    n+=1
    for (kind,k,w,ox),(_,_,_,op) in zip(rx,rp):
        c=DA.cls(xd[ox:ox+4],pd[op:op+4]); s=stat[(kind,w)]
        if c in (0,DA.ALL):
            if c==0: s[2]['nonperm']+=1
            continue
        s[0]+=1; s[1]&=c
        s[2][tuple(DA.NAMES[j] for j in range(5) if c>>j&1)]+=1
print('coppie con regioni uguali',n)
for kk,s in sorted(stat.items()): print(kk,'n',s[0],'rule',[DA.NAMES[j] for j in range(5) if s[1]>>j&1],dict(s[2].most_common(4)))
# DLC
bad=collections.Counter(); ex={}
for x,v in mats.items():
    if v['source']!='converted' or x not in DM: continue
    xd,xr=DM[x]; pd=v['data']
    import pickle
    # reloc PC: need; use xr layout assumption (same offsets if size equal)
    if len(pd)!=len(xd): continue
    xrel=R.parse(xr,'be'); rx=regions(xd,xrel,'>')
    for kind,k,w,o in rx:
        c=DA.cls(xd[o:o+4],pd[o:o+4]); s=stat[(kind,w)]
        if s[0]<5 or c in (0,DA.ALL): continue
        if not (c&s[1]): bad[(kind,w)]+=1; ex.setdefault((kind,w),[]).append((x,k,xd[o:o+4].hex(),pd[o:o+4].hex()))
print('DLC bad',dict(bad))
for kk,v in ex.items(): print(kk,v[:5])
