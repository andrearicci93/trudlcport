import sys, os
sys.path.insert(0,'tools')
import dtp_audit as A, drm_write as DW, drm_reloc as R, struct
rel=sys.argv[1]; sid=int(sys.argv[2]); offs=[int(x,0) for x in sys.argv[3:]]
files=A.overlay(A.INSTALLED+['mods_fix20','chain_aim/mods_chainfix_min'])
path=files[rel]; print(path)
xs=A.xsecs(rel); D=DW.read(open(path,'rb').read(),'le')
for x,i in A.section_pairs(xs,D):
    s=D.sections[i]
    if s.id==sid and x['type']==7:
        print('xid',x['id'],'len',len(x['data']),len(s.data))
        xr=R.parse(x['reloc'],'be')
        ptr=set(xr.pointer_offsets()); idl=set(xr.id_offsets())
        for o in offs:
            for k in range(o-16,o+32,4):
                print('%#x %s xbox %s pc %s %s'%(k, x['data'][k:k+4].hex(), '', s.data[k:k+4].hex(), 'P' if k in ptr else 'I' if k in idl else ''))
            print()
