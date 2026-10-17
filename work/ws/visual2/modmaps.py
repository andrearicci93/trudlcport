import sys,collections,struct
sys.path.insert(0,'/path/to/trudlcport/tools')
import material_reslot as MR
from shaderlib import constants
L=MR.libs(); X,D,P,DM=L['X'],L['D'],L['P'],L['DM']
mats,msh,mx2p=MR.dlc_tables()
def names(lib,plat):
    s=set()
    if lib:
        for sl in set(lib['slots'])-{0xFFFFFFFF}:
            v,c=constants(lib['entries'][sl]['blob'],plat)
            for n,rs,ri,rc in c: s.add(n)
    return s
def kw(ns,k): return any(k in n for n in ns)
c=collections.Counter(); rows=[]
for x,v in mats.items():
    if v['source']!='converted' or x not in DM: continue
    xt=struct.unpack_from('>4I',DM[x][0],0x28); pt=struct.unpack_from('<4I',v['data'],0x28)
    xn=set().union(*[names(D.get(s,X.get(s)),'x') for s in xt if s]) ; pn=set().union(*[names(P.get(s),'p') for s in pt if s])
    for k in ('Modulation','ShadowMap','Attenuation','Irradiance','p_Lights','LightEnabled','Ambient','SunLight','Setup'):
        c[(k,kw(xn,k),kw(pn,k))]+=1
for k,v in sorted(c.items()): print(k,v)
