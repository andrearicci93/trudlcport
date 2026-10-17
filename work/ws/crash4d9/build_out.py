import sys,hashlib,os,struct
sys.path.insert(0,'/path/to/trudlcport/tools')
import drm_write as DW
B='/path/to/trudlcport/work/baseline/B10/mods/'
jobs=[('dlc_caverns_hall.drm','dlc_caverns_hall.drm'),('StreamGroups/dlc_water_wheel_waterWheel_main.drm','dlc_water_wheel_waterwheel_main.drm')]
import glob
for src,_ in jobs:
    p=B+src
    if not os.path.exists(p):
        p=[x for x in glob.glob(B+'StreamGroups/*') if x.lower()==(B+src).lower()][0]
    raw=open(p,'rb').read()
    D=DW.read(raw,'le')
    assert D.write('le')==DW.cdrm_decode(raw,'le')
    n=0
    for s in D.sections:
        if s.type==10 and s.id==23397:
            pd=bytearray(s.data); T=struct.unpack_from('<I',pd,0)[0] if False else None
            # texture list offset: first idref type5
            import drm_reloc as R
            rel=R.parse(s.reloc,'le'); T=dict(rel.internal)[0x54]
            assert (pd[0x50],pd[0x51],pd[0x52])==(2,9,9)
            e8=bytes(pd[T+16*8:T+16*9]); e9=bytes(pd[T+16*9:T+16*10])
            assert struct.unpack_from('<I',e8,8)[0]==5 and struct.unpack_from('<I',e9,8)[0]==4
            pd[T+16*8:T+16*9]=e9; pd[T+16*9:T+16*10]=e8
            s.data=bytes(pd); n+=1
    assert n==1
    out=DW.cdrm_encode(D.write('le'),'le')
    name=os.path.basename(p)
    sub='StreamGroups/' if 'StreamGroups' in p else ''
    os.makedirs('out/'+sub,exist_ok=True)
    open('out/'+sub+name,'wb').write(out)
    print(sub+name,hashlib.md5(out).hexdigest(),len(out),len(raw))
