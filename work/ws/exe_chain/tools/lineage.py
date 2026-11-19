"""lineage.py: per ogni exe distinto (md5) trova il 'genitore' piu' vicino (min byte diversi nel file) tra quelli piu' vicini al vanilla."""
import sys, hashlib, numpy as np, os
ROOT='C:/tru-port/'
lst=[l.split(None,1) for l in open(ROOT+'work/ws/exe_chain/md5_sorted.txt')]
seen={}; 
for m,p in lst:
    p=p.strip()
    if p.startswith('/c/Program'): continue
    seen.setdefault(m,p)
names={m:p for m,p in seen.items()}
data={}
L=0
for m,p in names.items():
    b=open(ROOT+p,'rb').read(); data[m]=b; L=max(L,len(b))
arr={m:np.frombuffer(b+bytes(L-len(b)),dtype=np.uint8) for m,b in data.items()}
V='56d1ce2dffa62f16354063da2df44d5a'
dv={m:int((arr[m]!=arr[V]).sum()) for m in arr}
order=sorted(arr,key=lambda m:dv[m])
for m in order:
    if m==V: continue
    best=None
    for c in order:
        if c==m or dv[c]>dv[m]: continue
        n=int((arr[m]!=arr[c]).sum())
        if best is None or n<best[0]: best=(n,c)
    print('%s %8d %-55s <- %s %7d %s'%(m[:8],dv[m],names[m],best[1][:8],best[0],names[best[1]]))
