import sys,os,struct
sys.path.insert(0,'tools')
import drm_write as DW
T=os.path.expanduser('~/Downloads/tru-port/work/')
files={'gw_current':'mods_current/dlc1_ei_grapple_wall.drm','gw_glitchfix2':'mods_glitchfix2/dlc1_ei_grapple_wall.drm','ds_fix20':'mods_fix20/dlc1_uo_dragon_slider.drm','ds_fix16':'mods_fix16/dlc1_uo_dragon_slider.drm','ds_rc':'mods_dlc1_rc/dlc1_uo_dragon_slider.drm','gw_rc':'mods_dlc1_rc/dlc1_ei_grapple_wall.drm'}
mid=int(sys.argv[1]) if len(sys.argv)>1 else 21164
S={}
for k,f in files.items():
    p=T+f
    if not os.path.exists(p): print(k,'missing'); continue
    D=DW.read(open(p,'rb').read(),'le')
    for s in D.sections:
        if s.type==10 and s.id==mid: S[k]=bytes(s.data); print(k,len(s.data),[ (hex(o),) for o in []])
ks=list(S)
base=S[ks[0]]
for k in ks:
    d=S[k]
    diff=[i for i in range(0,min(len(d),len(base)),4) if d[i:i+4]!=base[i:i+4]]
    print(k,len(d),'vs',ks[0],[hex(i) for i in diff])
    print('   tex entries @0x4f0..',[d[o:o+16].hex() for o in range(0x4f0,0x530,16)] if len(d)>0x530 else '')
