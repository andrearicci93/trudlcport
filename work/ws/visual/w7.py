import sys,struct,collections
sys.path.insert(0,'/path/to/trudlcport/tools')
import material_reslot as MR
L=MR.libs(); P=L['P']; PM=L['PM']; DM=L['DM']
def has_bb(pt):
    regs=MR.union_regs([P.get(s) if s else None for s in pt[:3]],'p',keys=[('p',s) for s in pt[:3]])
    names=set().union(*regs.values()) if regs else set()
    return any('BackBuffer' in n or 'DepthBuffer' in n for n in names)
c=collections.Counter(); ex=collections.defaultdict(list)
for k,(d,r) in PM.items():
    pt=struct.unpack_from('<4I',d,0x28); b=has_bb(pt); v=struct.unpack_from('<I',d,0x38)[0]
    c[(b,v)]+=1; ex[(b,v)].append(k)
print(sorted(c.items()))
for kk in ex:
    if kk[0]: print(kk,ex[kk][:15])
print('--- BB+Depth+Normal')
def names(pt):
    regs=MR.union_regs([P.get(s) if s else None for s in pt[:3]],'p',keys=[('p',s) for s in pt[:3]])
    return set().union(*regs.values()) if regs else set()
c=collections.Counter(); ex=collections.defaultdict(list)
for k,(d,r) in PM.items():
    pt=struct.unpack_from('<4I',d,0x28); n=names(pt)
    key=(any('BackBuffer' in x for x in n),any('Depth' in x for x in n),any('Normal' in x for x in n))
    v=struct.unpack_from('<I',d,0x38)[0]; c[(key,v)]+=1; ex[(key,v)].append(k)
for kk,v in sorted(c.items()):
    if kk[0][0] or kk[0][1]: print(kk,v,ex[kk][:8])
print('--- DLC xbox mats with 20263-like (xt 1450):')
import json
for k,(d,r) in DM.items():
    pass
print('=== DLC (converted PC mats from dlc_materials_pc.pkl)')
mats,msh,mx2p=MR.dlc_tables()
c=collections.Counter(); ex=collections.defaultdict(list)
for k,m in mats.items():
    d=m['data']; pt=struct.unpack_from('<4I',d,0x28); n=names(pt)
    bb=any('BackBuffer' in x for x in n); dp=any('Depth' in x for x in n)
    v=struct.unpack_from('<I',d,0x38)[0]; xv=None
    if k in DM: xv=struct.unpack_from('>I',DM[k][0],0x38)[0]
    c[(bb,dp,v,m['source'])]+=1; ex[(bb,dp,v,m['source'])].append((k,pt[:3]))
for kk,v in sorted(c.items()):
    if kk[0] or kk[1]: print(kk,v,ex[kk][:6])
