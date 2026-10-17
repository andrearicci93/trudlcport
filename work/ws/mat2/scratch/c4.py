import sys
sys.path.insert(0,'tools')
import drm_write as DW, drm_reloc as R, struct
a=DW.read(open('work/mods_dlc1_rc/dlc1_uo_bend_switches.drm','rb').read(),'le'); b=DW.read(open('work/ws/mat2/out/dlc1_uo_bend_switches.drm','rb').read(),'le')
print(len(a.sections),len(b.sections))
ch=[(x.type,x.id) for x,y in zip(a.sections,b.sections) if bytes(x.data)!=bytes(y.data) or bytes(x.reloc or b'')!=bytes(y.reloc or b'')]
print('changed sections',ch)
for y in b.sections:
    if y.id==21210 and y.type==10:
        rel=R.parse(y.reloc,'le'); print(R.check(rel,len(y.data)), struct.unpack_from('<I',y.data,0x58))
