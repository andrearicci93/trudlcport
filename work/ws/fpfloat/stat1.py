import sys, pickle, collections
sys.path.insert(0,'work/ws/fpfloat'); sys.path.insert(0,'tools')
from feat import *
CONF=[]  # (depth, useshape)
for d in (1,2,3):
    for s in (0,1): CONF.append((d,s))
st=[[collections.defaultdict(lambda:[0]*6) for _ in CONF] for _ in range(2)]
meta=0
for x,p,xb,pc,xr in A.base_pairs():
    f=A.fold(xb['src']); xd=xb['data']; pd=pc['data']
    for o,k,ks,sh in words(xd,xr):
        c=A.cls(xd[o:o+4],pd[o:o+4])
        if c==A.ALL or c==0: continue
        for ci,(d,us) in enumerate(CONF):
            v=st[f][ci][(k,ks[d-1],sh if us else 0)]; v[0]+=1
            for i in range(5):
                if c>>i&1: v[i+1]+=1
pickle.dump(([dict(a) for a in st[0]],[dict(a) for a in st[1]],CONF),open('work/ws/fpfloat/stat1.pkl','wb'))
print('done')
