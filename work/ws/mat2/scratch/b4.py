import sys,struct,collections,pickle,json
sys.path.insert(0,'tools')
import material_reslot as MR
from shaderlib import constants
L=MR.libs(); X,D,P,XM,PM,DM=[L[k] for k in 'XDPXMPMDM'.replace('XM','X')] if False else (L['X'],L['D'],L['P'],L['XM'],L['PM'],L['DM'])
# Xbox: names of consts
c=collections.Counter()
for sid,lib in list(X.items())[:400]:
    if lib['kind']!=1: continue
    for s in set(lib['slots'])-{0xFFFFFFFF}:
        v,cs=constants(lib['entries'][s]['blob'],'x')
        for n,rs,ri,rc in cs:
            if 'Param' in n or 'Opacity' in n: c[(n,rs,ri,rc)]+=1
print(sorted(c.items())[:40])
