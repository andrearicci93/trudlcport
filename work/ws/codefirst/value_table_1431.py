"""Valori Xbox dei candidati nelle 8 materiali DLC (1431,1060) + materiale ponte: ruolo strutturale vs distribuzione numerica."""
import sys; sys.path.insert(0,'/path/to/trudlcport/work/ws/shader4'); sys.path.insert(0,'/path/to/trudlcport/work/ws/codefirst')
from f12_build_all import *
L=libs(); DM=L['DM']
cols=[(109,0),(109,1),(107,0),(107,1),(107,2),(107,3),(100,3)]
print('mat    '+' '.join(('c%d.%s'%(r,'xyzw'[c])).rjust(8) for r,c in cols))
for mid in (20344,21093,21258,22596,22597,23186,23437,24043):
    XP=params(f9_common._Sec(*DM[mid]),'be'); print('%-6d '%mid+' '.join(('%8.4g'%XP[r-100][c]) if r-100<len(XP) else '       -' for r,c in cols))
