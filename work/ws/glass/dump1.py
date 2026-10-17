import sys
sys.path.insert(0,'/path/to/trudlcport/tools')
from drm import cdrm_decode, sections_with_data
import tex_convert as T
from PIL import Image
R='/path/to/trudlcport/work/'
raw=cdrm_decode(open(R+'mods_dlc1_rc/dlc_water_wheel.drm','rb').read(),'le')
h,secs=sections_with_data(raw,'le')
for s in secs:
    if s['type']==5 and s['id'] in (158,1207,1206,144,157):
        im=T.pc_image(s['data']); 
        Image.fromarray(im).save('png/ww_pc_%d.png'%s['id']); print(s['id'],im.shape,T.parse_pc(s['data']),s['spec'],s['nreloc'],len(s['data']))
