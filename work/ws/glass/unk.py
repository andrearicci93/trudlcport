import sys
sys.path.insert(0,'/path/to/trudlcport/tools')
from archive import Archive
from drm import cdrm_decode, sections_with_data
from names import crc
import mesh_convert as MC
X=Archive('/path/to/Xenia-SteveRepack/Content/534307EC/00000002/9CA70CF0EDA43654D158C2E37470D301DFA850E753/pack10.000','be')
for rel in ['streamgroups\\dlc_water_wheel_waterwheel_main.drm','dlc1_uo_water_wheel.drm','dlc_caverns_hall.drm','dlc_caverns.drm','dlc_water_wheel.drm']:
    rec=X.find(crc('xenon-w\\'+rel)); raw=cdrm_decode(X.read(rec[0]),'be'); _,secs=sections_with_data(raw,'be')
    for s in secs:
        if s['type']==12 and s['data'][0x10:0x14]==b'hseM':
            info={}; MC.convert(s['data'],s['reloc'],None,info)
            print(rel,s['id'],'unknown',info['unknown_decls'],'rebatched',info['rebatched'])
