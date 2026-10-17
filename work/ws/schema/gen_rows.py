import sys; sys.path.insert(0,'/path/to/trudlcport/work/ws/schema')
from derive import *
def inf(xw,start,size,typ):
    if typ=='u8': return any(xw[m]!=xw[start] for m in range(4) if m!=start)
    if typ=='u16': return xw[start]!=xw[start+1]
    if typ=='u32': return xw[0]!=xw[3] or xw[1]!=xw[2]
    return False
smp=collect()
rows={}
for (st,off) in sorted(smp):
    inter,n,nd,exc,excs=derive(smp[st,off])
    fl=fields(inter) if n else None
    if fl is None: fl=[(0,4,'UNK')]
    # merge consecutive UNK bytes
    out=[]
    for (j,sz,t) in fl:
        if t=='UNK':
            if out and out[-1][2]=='UNK': out[-1]=(out[-1][0],out[-1][1]+sz,'UNK')
            else: out.append((j,sz,'UNK'))
        else: out.append((j,sz,t))
    for (j,sz,t) in out:
        if t=='UNK': rows.setdefault(st,[]).append((off+j,sz,'UNKNOWN_RAW',0,0,0)); continue
        ni=0; dd=set()
        for xw,pw,key in smp[st,off]:
            c=cls(xw,pw)
            if len(c)==5 or not c: continue
            if inf(xw,j,sz,t): ni+=1; dd.add(key)
        rows.setdefault(st,[]).append((off+j,sz,t,ni,len(dd),exc))
for st,r in rows.items():
    print('#',st)
    for x in r: print(x)
import json; json.dump(rows,open('/path/to/trudlcport/work/ws/schema/rows.json','w'))
