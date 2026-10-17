import sys; sys.path.insert(0,'/path/to/trudlcport/work/ws/schema')
from lib import *
import pickle, collections
def is_ascii_ptr(xd, t):
    if t is None or t>=len(xd): return False
    z=xd.find(b'\0',t,t+64)
    return z>t and all(32<=c<127 for c in xd[t:z])
def descs(xd, rel):
    it=dict(rel.internal)
    out=[]
    for o8,t1 in it.items():
        o=o8-8
        if o<0 or o+0x54>len(xd): continue
        if (o+0x10) not in it: continue
        n=struct.unpack_from('>I',xd,o+4)[0]
        if not 1<=n<=64: continue
        if t1+28*n>len(xd): continue
        if not all(is_ascii_ptr(xd,it.get(t1+28*k+8)) for k in range(n)): continue
        ok=True
        for k in range(n):
            nb=t1+28*k
            nt=struct.unpack_from('>I',xd,nb+0xc)[0]; na=struct.unpack_from('>I',xd,nb+0x14)[0]
            if nt>64 or na>64: ok=False;break
            if nt and (it.get(nb+0x10) is None or any((it[nb+0x10]+4*q) not in it for q in range(nt))): ok=False;break
        if ok: out.append(o)
    return sorted(out)
if __name__=='__main__':
    pairs=pickle.load(open(T+'/work/generic/pairs.pkl','rb'))
    tot=0; res=[]
    for name,((xh,xs),(ph,ps)) in pairs.items():
        for s in xs:
            if s['type']!=7 or s['data'] is None: continue
            r=R.parse(s['reloc'],'be')
            d=descs(s['data'],r)
            if d: res.append((name,s['id'],d,len(s['data']))); 
    print(len(res)); 
    for r in res[:60]: print(r[0][-40:],r[1],[hex(x) for x in r[2]],r[3])
