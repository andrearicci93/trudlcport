import sys,collections
sys.path.insert(0,'tools')
import material_reslot as MR
from shaderlib import constants
L=MR.libs(); P=L['P']
c=collections.Counter()
for pid,lib in P.items():
    if lib['kind']!=1: continue
    for s in set(lib['slots'])-{0xFFFFFFFF}:
        v,cs=constants(lib['entries'][s]['blob'],'p')
        for n,rs,ri,rc in cs:
            if rs==2 and 98<=ri<160: c[(n,ri)]+=1
print(sorted(c.items(),key=lambda kv:kv[0][1]))
