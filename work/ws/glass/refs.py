import sys,struct,collections
sys.path.insert(0,'/path/to/trudlcport/tools')
from drm import cdrm_decode, sections_with_data
import drm_reloc as R
Rt='/path/to/trudlcport/work/mods_dlc1_rc/'
files=['dlc_water_wheel.drm','streamgroups/dlc_water_wheel_waterwheel_main.drm','dlc1_uo_water_wheel.drm','dlc_caverns.drm']
atl={6712,6714,6716,6718,6720,6722,6724,6726,6728,6556,6766,7056,6757}
for f in files:
    raw=cdrm_decode(open(Rt+f,'rb').read(),'le'); _,secs=sections_with_data(raw,'le')
    c=collections.Counter()
    for s in secs:
        if s['type']==5 or not s['reloc']: continue
        try: rel=R.parse(s['reloc'],'le')
        except Exception as e: continue
        for t,o in rel.idref+rel.idref_a:
            if t==5 and o+4<=len(s['data']):
                v=struct.unpack_from('<I',s['data'],o)[0]
                if v in atl: c[(s['type'],s['id'],v)]+=1
    print(f,dict(c))
