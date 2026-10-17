import sys,os,struct
sys.path.insert(0,'/path/to/trudlcport/tools')
from drm import cdrm_decode, sections_with_data
import material_reslot as MR
L=MR.libs(); P=L['P']
def bbd(pt):
    regs=MR.union_regs([P.get(s) if s else None for s in pt[:3]],'p',keys=[('p',s) for s in pt[:3]])
    n=set().union(*regs.values()) if regs else set()
    return any('BackBuffer' in x for x in n) and any('Depth' in x for x in n)
B='/path/to/trudlcport/work/baseline/B11/mods/'
for dp,dn,fn in os.walk(B):
    for f in fn:
        if not f.endswith('.drm'): continue
        p=os.path.join(dp,f)
        try:
            raw=cdrm_decode(open(p,'rb').read(),'le'); _,secs=sections_with_data(raw,'le')
        except Exception as e: continue
        for s in secs:
            if s['type']==10 and s['id']>=15000:
                d=s['data']; pt=struct.unpack_from('<4I',d,0x28)
                if bbd(pt): print(os.path.relpath(p,B),s['id'],pt[:3],'0x38=',struct.unpack_from('<I',d,0x38)[0])
