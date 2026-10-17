import sys,struct,collections,pickle
sys.path.insert(0,'tools')
import material_reslot as MR
import mat2_params_count as M
from d3d9_consts import used_consts
L=MR.libs(); P,PM,XM=L['P'],L['PM'],L['XM']
mid=21210
mats,msh,mx2p=MR.dlc_tables()
m=mats[mid]; print(m['flags'],msh.get(mid))
pt=struct.unpack_from('<4I',m['data'],0x28); print(pt)
for s in pt[:3]:
    print(s,M.lib_need(P[s],('p',s)) if s in P else None)
# base PC materials with same ps lib 335/337
for pid,(d,r) in PM.items():
    t=struct.unpack_from('<4I',d,0x28)
    if t[0]==335 or t[2]==337 : print('base',pid,t,struct.unpack_from('<I',d,0x58)[0])
