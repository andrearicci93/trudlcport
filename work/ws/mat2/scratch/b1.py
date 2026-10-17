import sys,struct,collections,pickle,json
sys.path.insert(0,'tools')
import material_reslot as MR
from shaderlib import constants
L=MR.libs(); P=L['P']; X=L['X']
print(L.keys())
for pid in (205,206,207,208):
    lib=P[pid]; print(pid,lib['kind'],len(set(lib['slots'])-{0xFFFFFFFF}))
    cs=collections.Counter()
    for s in set(lib['slots'])-{0xFFFFFFFF}:
        v,c=constants(lib['entries'][s]['blob'],'p')
        for n,rs,ri,rc in c: cs[(n,rs,ri,rc)]+=1
    for k,v in sorted(cs.items(),key=lambda kv:(kv[0][1],kv[0][2])): print('  ',k,v)
