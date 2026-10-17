import sys,struct,collections
sys.path.insert(0,'/path/to/trudlcport/work/ws/rings')
from inst import *
import uidmap
M=uidmap.allmap()
p=u32(0xd98d54); cnt=0; rows=[]
while p and cnt<5000:
    od=u32(p+0x10); cnt+=1
    uid=u32(p+0x58); par=u32(p+0x4c)
    nm=(u32(od+0x3a)&0xffff) if od else 0
    npts=0; types=[]
    if od and nm and nm<20:
        ml=u32(od+0x40)
        for j in range(nm):
            mdl=u32(ml+4*j)
            if not mdl: continue
            n=u32(mdl+0x5c)
            if n and n<50:
                pa=u32(mdl+0x60); npts+=n
                for q in range(n): types.append(u32(pa+32*q)>>16)
    rows.append((p,od,uid,par,u32(p+0x14),npts,types))
    p=u32(p+8)
print(len(rows))
cc=collections.Counter()
for p,od,uid,par,fl,npts,types in rows:
    if uid is not None and uid<0x4000 and 9400<=uid<=11000 and par==0:
        e=M.get(uid)
        print(hex(p),'def',hex(od or 0),'uid',uid,e[0][0:2] if e else None,'flags',hex(fl),'pts',npts,types)
