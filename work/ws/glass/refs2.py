import sys,struct,collections,pickle
sys.path.insert(0,'/path/to/trudlcport/tools')
from drm import cdrm_decode, sections_with_data
import drm_reloc as R
tex=pickle.load(open('tex_table.pkl','rb'))
Rt='/path/to/trudlcport/work/'
files=[Rt+'mods_dlc1_rc/dlc_water_wheel.drm',Rt+'mods_dlc1_rc/streamgroups/dlc_water_wheel_waterwheel_main.drm',Rt+'mods_dlc1_rc/dlc1_uo_water_wheel.drm',Rt+'mods_fix20/dlc_caverns_hall.drm',Rt+'mods_dlc1_rc/dlc_caverns.drm']
for f in files:
    raw=cdrm_decode(open(f,'rb').read(),'le'); _,secs=sections_with_data(raw,'le')
    for s in secs:
        if s['type'] in (5,10,12) or not s['reloc']: continue
        try: rel=R.parse(s['reloc'],'le')
        except: continue
        ids=[]
        for t,o in rel.idref+rel.idref_a:
            if t==5 and o+4<=len(s['data']): ids.append((struct.unpack_from('<I',s['data'],o)[0],hex(o)))
        if ids: print(f.split('/')[-1],'sec type',s['type'],'id',s['id'],ids[:12])
