"""hdr_map.py - per campo header materiale (0x00..0x7F): mappa valore Xbox -> valore PC sulle coppie base; poi controlla i materiali DLC convertiti."""
import sys,struct,collections,pickle
sys.path.insert(0,'/path/to/trudlcport/tools')
import material_reslot as MR, drm_reloc as R
L=MR.libs(); XM,PM,DM=L['XM'],L['PM'],L['DM']
mats,msh,mx2p=MR.dlc_tables()
def W(d,e,o): return struct.unpack_from(e+'I',d,o)[0]
m=collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
n=0
for xid,(xd,xr) in XM.items():
    p=mx2p.get(xid)
    if p not in PM: continue
    pd=PM[p][0]
    if len(pd)!=len(xd): continue
    n+=1
    for o in range(0,0x80,4):
        m[o][W(xd,'>',o)][W(pd,'<',o)]+=1
print('coppie',n)
conv=[(x,v) for x,v in mats.items() if v['source']=='converted' and x in DM]
print('DLC convertiti',len(conv))
for o in range(0,0x80,4):
    tot=sum(sum(c.values()) for c in m[o].values()); nv=len(m[o])
    # determinismo
    det=sum(max(c.values()) for c in m[o].values())
    # dlc
    bad=[];unk=0
    for x,v in conv:
        xd=DM[x][0]; pd=v['data']
        xv=W(xd,'>',o); pv=W(pd,'<',o)
        c=m[o].get(xv)
        if c is None: unk+=1; continue
        if pv not in c: bad.append((x,xv,pv,dict(c)))
    print('0x%02x xvals %d det %.4f  dlc: unk %d bad %d'%(o,nv,det/tot,unk,len(bad)), bad[:3] if bad and len(bad)<2000 else '')
print('---- tabelle')
for o in (0x38,0x3c,0x44,0x48,0x68):
    print(hex(o),{hex(k):{hex(a):b for a,b in c.items()} for k,c in m[o].items()})
