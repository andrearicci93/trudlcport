import sys,os,struct,collections,pickle
sys.path.insert(0,'/path/to/trudlcport/tools')
import numpy as np
from drm import cdrm_decode, sections_with_data
import tex_convert as T, drm_reloc as R, material_reslot as MR
Rt='/path/to/trudlcport/work/'
files={'ww':Rt+'mods_dlc1_rc/dlc_water_wheel.drm','wwmain':Rt+'mods_dlc1_rc/streamgroups/dlc_water_wheel_waterwheel_main.drm','uo':Rt+'mods_dlc1_rc/dlc1_uo_water_wheel.drm','hall':Rt+'mods_dlc1_rc/dlc_caverns.drm'}
tex={};mats=[]
for k,f in files.items():
    raw=cdrm_decode(open(f,'rb').read(),'le'); h,secs=sections_with_data(raw,'le')
    for s in secs:
        if s['type']==5:
            hd=T.parse_pc(s['data'])
            try:
                im=T.pc_image(s['data']); rgb=im[...,:3].astype(float)
                sat=(rgb.max(2)-rgb.min(2)).mean(); 
                tex[s['id']]=(k,hd['w'],hd['h'],hex(hd['fmt']),hd['mips'],round(sat,1),rgb.reshape(-1,3).mean(0).round().astype(int).tolist())
            except Exception as e: tex[s['id']]=(k,'err',str(e))
        elif s['type']==10: mats.append((k,s))
pickle.dump(tex,open('tex_table.pkl','wb'))
print(len(tex),len(mats))
for k,s in mats:
    rel=R.parse(s['reloc'],'le')
    es=MR.tex_entries(s['data'],rel,'<')
    line=[]
    for o,tid,ty,slot in es:
        t=tex.get(tid)
        line.append('%d:ty%d@%d %s'%(tid,ty,slot,('%sx%s %s s%s'%(t[1],t[2],t[3],t[5]) if t and len(t)>3 else str(t))))
    print(k,s['id'],' | '.join(line))
