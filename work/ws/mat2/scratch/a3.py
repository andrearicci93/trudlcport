import sys,struct
sys.path.insert(0,'tools')
import drm_write as DW, drm_reloc as R
for f in ('mods_dlc1_rc/dlc1_uo_dragon_slider.drm','mods_current/dlc1_ei_grapple_wall.drm'):
    D=DW.read(open('work/'+f,'rb').read(),'le')
    print(f)
    for s in D.sections:
        if s.type in (12,) and s.reloc:
            rel=R.parse(s.reloc,'le')
            for t,o in rel.idref+rel.idref_a:
                v=struct.unpack_from('<I',s.data,o)[0]
                if t==10 and v in(21164,): print(' mesh',s.id,'ref type',t,v,'at',hex(o))
    print(' types',sorted({(s.type) for s in D.sections}))
