import sys,os,json
sys.path.insert(0,'/path/to/trudlcport/tools')
import numpy as np
from drm import cdrm_decode, sections_with_data
import tex_convert as T
from PIL import Image
R='/path/to/trudlcport/work/'
files={'ww':R+'mods_dlc1_rc/dlc_water_wheel.drm','wwmain':R+'mods_dlc1_rc/streamgroups/dlc_water_wheel_waterwheel_main.drm','uo':R+'mods_dlc1_rc/dlc1_uo_water_wheel.drm','hall':R+'mods_dlc1_rc/dlc_caverns.drm'}
import glob
for k,f in files.items():
    if not os.path.exists(f): print('missing',f); continue
    raw=cdrm_decode(open(f,'rb').read(),'le')
    h,secs=sections_with_data(raw,'le')
    from collections import Counter
    print(k,len(secs),Counter(s['type'] for s in secs))
    rows=[]
    for s in secs:
        if s['type']!=5: continue
        try:
            hd=T.parse_pc(s['data']); im=T.pc_image(s['data'])
        except Exception as e:
            print(' err',s['i'],hex(s['id']),e); continue
        a=im[...,:3].astype(float)
        nz=(np.abs(np.diff(a,axis=1)).mean()+np.abs(np.diff(a,axis=0)).mean())/2
        rows.append((nz,s['i'],s['id'],hd['w'],hd['h'],hex(hd['fmt']),hd['mips'],hd['flags']))
    rows.sort(reverse=True)
    print(' ntex',len(rows))
    for r in rows[:15]: print('  ',r)
