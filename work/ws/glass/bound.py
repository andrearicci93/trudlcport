import sys,struct,pickle,collections
sys.path.insert(0,'/path/to/trudlcport/tools')
from drm import cdrm_decode, sections_with_data
import drm_reloc as R, material_reslot as MR
L=MR.libs(); P=L['P']
tex=pickle.load(open('tex_table.pkl','rb'))
Rt='/path/to/trudlcport/work/'
files=[Rt+'mods_dlc1_rc/dlc_water_wheel.drm',Rt+'mods_dlc1_rc/streamgroups/dlc_water_wheel_waterwheel_main.drm',Rt+'mods_dlc1_rc/dlc1_uo_water_wheel.drm',Rt+'mods_fix20/dlc_caverns_hall.drm']
want=set(int(x) for x in sys.argv[1:]) if len(sys.argv)>1 else None
done=set()
for f in files:
    raw=cdrm_decode(open(f,'rb').read(),'le'); _,secs=sections_with_data(raw,'le')
    for s in secs:
        if s['type']!=10 or s['id'] in done: continue
        if want and s['id'] not in want: continue
        done.add(s['id'])
        d=s['data']; rel=R.parse(s['reloc'],'le')
        pt=struct.unpack_from('<4I',d,0x28)
        plibs=[P.get(x) if x else None for x in pt[:3]]
        br=MR.bound_report(d,s['reloc'],plibs,pkeys=[('p',x) for x in pt[:3]])
        es={slot:(tid,ty) for o,tid,ty,slot in MR.tex_entries(d,rel,'<')}
        print('MAT',s['id'],'tuple',[hex(x) for x in pt])
        for r,ns,ty in br:
            e=es.get(r); t=tex.get(e[0]) if e else None
            print('   reg',r,sorted(ns)[:2],'entry',e,(t[1:6] if t and len(t)>3 else t))
        for slot,(tid,ty) in es.items():
            if slot not in [b[0] for b in br]: print('   unsampled slot',slot,tid,ty)
