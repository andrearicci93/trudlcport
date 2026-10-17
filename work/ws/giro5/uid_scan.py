"""Intro.uniqueID >= 16352 (limite dead bits 0x7fc*8) nei DRM unita' di una baseline + massimo nel PC base."""
import sys,os,struct,glob
T='/path/to/trudlcport/tools'; sys.path.insert(0,T)
import drm, unit_ids as U
R='/path/to/trudlcport/work/baseline/'
base=sys.argv[1] if len(sys.argv)>1 else 'B87_materiali19'
LIM=0x7fc*8
for p in sorted(glob.glob(R+base+'/mods/**/*.drm',recursive=True)):
    try: sc=drm.sections_with_data(drm.cdrm_decode(open(p,'rb').read(),'le'),'le')[1]; Lv=U.level_info(sc,'le')
    except Exception as e: continue
    if not Lv or not Lv['intros']: continue
    ids=[]
    for si,o in Lv['intros']:
        d=sc[si]['data']; ids.append((struct.unpack_from('<I',d,o+0x58)[0],struct.unpack_from('<H',d,o+0x50)[0]))
    hi=[i for i in ids if i[0]>=LIM]
    print(os.path.relpath(p,R+base+'/mods'),'intro',len(ids),'max uid',max(i[0] for i in ids),'min',min(i[0] for i in ids),'>=LIM:',hi[:12],len(hi))
