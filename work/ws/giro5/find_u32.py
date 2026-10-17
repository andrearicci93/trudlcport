"""Cerca valori u32 (LE/BE) in sezioni di un DRM. Uso: find_u32.py BASE|XBOX file.drm v1,v2,.. [tipi]"""
import sys,struct,os
sys.path.insert(0,'/path/to/trudlcport/tools'); sys.path.insert(0,'/path/to/trudlcport/work/ws/giro5')
import drm
R='/path/to/trudlcport/work/baseline/'
base,name=sys.argv[1],sys.argv[2]; vals=[int(x) for x in sys.argv[3].split(',')]
if base=='XBOX':
    from intros import *
    from archive import Archive
    from names import load,L
    C='/path/to/Xenia-SteveRepack/Content/534307EC/00000002/'; xn=load(L+'Tomb Raider Underworld (Xenon).txt'); raw=None
    for pk in [C+'9CA70CF0EDA43654D158C2E37470D301DFA850E753/pack10.000',C+'600A12643FCDAC84003E6E0DBD0A1A8F7DAE9DD153/pack11.000']:
        A=Archive(pk,'be')
        for r in A.idx:
            if xn.get(r['hash'],'').split('\\')[-1]==name: raw=drm.cdrm_decode(A.read(r),'be')
    sc=drm.sections_with_data(raw,'be')[1]; E='>'
else:
    sc=drm.sections_with_data(drm.cdrm_decode(open(R+base+'/mods/'+name,'rb').read(),'le'),'le')[1]; E='<'
for s in sc:
    d=s['data']
    if not d: continue
    for v in vals:
        pat=struct.pack(E+'I',v); i=-1
        while True:
            i=d.find(pat,i+1)
            if i<0: break
            if i%4==0: print('sez',s['i'],'type',s['type'],'id',s['id'],'off',hex(i),'val',v)
