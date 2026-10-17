import sys; sys.path.insert(0,'tools')
import struct, collections
import dtp_audit as A, drm_write as DW, drm_reloc as R, aidata_fix as AF
rel='dlc_caverns.drm'
files=A.overlay(A.INSTALLED+['mods_fix20'])
path=files[rel]; print(path)
xs=A.xsecs(rel); D=DW.read(open(path,'rb').read(),'le')
for x,i in A.section_pairs(xs,D):
    s=D.sections[i]
    if s.id==20872 and x['type']==7:
        xd=x['data']; pd=s.data; xr=R.parse(x['reloc'],'be')
        print(len(xd), 'reloc internal',len(xr.internal),'ptr',len(xr.pointer_offsets()),'id',len(xr.id_offsets()))
        ai=AF.detect(xd,xr); print('aidata',[hex(t) for t in ai])
        cl=collections.Counter()
        slots=set(xr.pointer_offsets())|set(xr.id_offsets())
        for o in range(0,len(xd)-3,4):
            if o in slots: cl['slot']+=1; continue
            c=A.cls(xd[o:o+4],pd[o:o+4])
            if c==A.ALL: cl['pal']+=1
            elif c==0: cl['none']+=1
            else: cl[tuple(A.NAMES[k] for k in range(5) if c>>k&1)]+=1
        print(cl)
        import hashlib
        # strings in data
        print([ (hex(a),xd[a:z]) for a,z,k in A.string_spans(xd,xr)][:50])
