import sys,struct,collections
sys.path.insert(0,'/path/to/trudlcport/work/ws/rings')
from inst import *
import uidmap
M=uidmap.allmap()
mg=u32(0xfadfac)
reg={}
if mg:
    for i in range(7):
        L=u32(mg+4*i)
        if not L: continue
        c34=u32(L+0x34); n=struct.unpack('<B',rb(c34+4,1))[0] if c34 else 0
        base=u32(L+0x38)
        hs=[u32(base+20*k) for k in range(n)]+[u32(L+0x3c)]
        for nd in hs:
            c=0
            while nd and c<500:
                hp=nd+8; p_=u32(hp); g=u32(hp+4)
                if p_ and u32(p_+0x44)==g: reg.setdefault(p_,[]).append((i,u32(nd+0x14),u32(nd+0x18)))
                nd=u32(nd+4); c+=1
print('mgr',hex(mg or 0),'list1 nodes',sum(1 for v in reg.values() for x in v if x[0]==1))
p=u32(0xd98d54); cnt=0
rows=[]
while p and cnt<8000:
    od=u32(p+0x10); uid=u32(p+0x58); par=u32(p+0x4c); cnt+=1
    did=u32(od+0x14) if od else None
    rows.append((p,od,uid,par,did))
    p=u32(p+8)
print('instances',cnt)
byp={r[0]:r for r in rows}
for p,od,uid,par,did in rows:
    e=M.get(uid)
    if par==0 and e and ('grapple' in e[0][1] or 'hpole' in e[0][1] or 'bend_sw' in e[0][1] or 'raft' in e[0][1]):
        kids=[r for r in rows if r[3]==p]
        print(hex(p),'uid',uid,e[0][0],e[0][1],'flags14 %x'%u32(p+0x14),'kids',[(hex(k[0]),'flags14=%x'%u32(k[0]+0x14),'reg=%s'%reg.get(k[0])) for k in kids],'self reg',reg.get(p))
print('--- flags +0x18 / +0x1c of registered list-1 instances')
for p,v in reg.items():
    if any(x[0]==1 for x in v):
        e=None
        par=u32(p+0x4c); uid=u32((par or p)+0x58)
        e=M.get(uid)
        f18=u32(p+0x18); f1c=u32(p+0x1c)
        print(hex(p),'uid',uid,e[0][1] if e else None,'f14=%x f18=%x f1c=%x'%(u32(p+0x14),f18,f1c),'valid_by_flags=%s'%(not (f1c&2) and not (f18&0x20000000)), 'handler',hex(u32(p+0x11c) or 0))
