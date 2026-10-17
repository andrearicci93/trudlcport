import sys,os,struct
sys.path.insert(0,'tools')
import drm_write as DW
T='work/'
def load(f): return DW.read(open(T+f,'rb').read(),'le')
a=load('mods_dlc1_rc/dlc1_uo_dragon_slider.drm'); b=load('mods_fix20/dlc1_uo_dragon_slider.drm')
print(len(a.sections),len(b.sections))
for x,y in zip(a.sections,b.sections):
    if (x.type,x.id)!=(y.type,y.id): print('ORDER',x.type,x.id,y.type,y.id); continue
    if bytes(x.data)!=bytes(y.data) or bytes(x.reloc or b'')!=bytes(y.reloc or b''):
        d=[i for i in range(0,min(len(x.data),len(y.data)),4) if x.data[i:i+4]!=y.data[i:i+4]]
        print('DIFF',x.type,x.id,len(x.data),len(y.data),len(d),[hex(i) for i in d[:10]])
# which meshes use 21164
for s in a.sections: print(s.type,s.id,len(s.data)) if s.type in (10,12) else None
