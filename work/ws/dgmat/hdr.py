import sys,struct,collections
sys.path.insert(0,'/path/to/trudlcport/tools')
import material_reslot as MR, drm_reloc as R
from drm import cdrm_decode, sections_with_data
L=MR.libs(); PM,XM,DM=L['PM'],L['XM'],L['DM']
mats,msh,mx2p=MR.dlc_tables()
T='/path/to/trudlcport/work/baseline/B8/mods/'
raw=cdrm_decode(open(T+'streamgroups/dlc_dungeon_dungeon_main.drm','rb').read(),'le'); _,secs=sections_with_data(raw,'le')
d={s['id']:s for s in secs if s['type']==10}
def tex(dd,rr): return [(t,ty,sl) for o,t,ty,sl in MR.tex_entries(dd,R.parse(rr,'le'),'<')]
b=PM[10918]
print('base 10918 tex',tex(*b))
for m in (20263,22619):
    x=d[m]['data']; print(m,'tex',tex(x,d[m]['reloc']))
    print(' diff hdr vs base',[(hex(i),b[0][i],x[i]) for i in range(0x58) if b[0][i]!=x[i]])
xd,xr=XM[15297]; print('xbox base hdr diff vs pc base',[(hex(i),xd[i],b[0][i]) for i in range(0x58) if xd[i]!=b[0][i]][:20])
xd2,xr2=DM[20263]; print('xbox 20263 vs xbox base',[(hex(i),xd[i],xd2[i]) for i in range(0x58) if xd[i]!=xd2[i]])
print('xbox base tex',[(t,ty,sl) for o,t,ty,sl in MR.tex_entries(xd,R.parse(xr,'be'),'>')], 'xbox 20263',[(t,ty,sl) for o,t,ty,sl in MR.tex_entries(xd2,R.parse(xr2,'be'),'>')])
# all PM materials with the BackBuffer samplers: value of u32 @0x48
