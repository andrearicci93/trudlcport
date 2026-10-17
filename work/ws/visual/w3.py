import sys,struct
sys.path.insert(0,'/path/to/trudlcport/tools')
import material_reslot as MR, drm_reloc as R
from drm import cdrm_decode, sections_with_data
L=MR.libs(); P=L['P']; PM=L['PM']
T='/path/to/trudlcport/work/baseline/B11/mods/'
def load(drm,mid):
    raw=cdrm_decode(open(T+drm,'rb').read(),'le'); _,secs=sections_with_data(raw,'le')
    s=[s for s in secs if s['type']==10 and s['id']==mid][0]; return s['data'],s['reloc']
def show(tag,d,r):
    pt=struct.unpack_from('<4I',d,0x28)
    print(tag,'tuple',pt)
    for o,tid,ty,slot in MR.tex_entries(d,R.parse(r,'le'),'<'): print('  entry tex',tid,'type',ty,'slot',slot)
    for x in MR.bound_report(d,r,[P.get(s) if s else None for s in pt[:3]],[('p',s) for s in pt[:3]]): print('  reg',x)
for mid in (20263,22619):
    d,r=load('streamgroups/dlc_dungeon_dungeon_main.drm',mid); show(mid,d,r)
show('base10918',*PM[10918])
