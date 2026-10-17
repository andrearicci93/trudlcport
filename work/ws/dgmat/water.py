import sys,os,struct,json
sys.path.insert(0,'/path/to/trudlcport/tools')
import material_reslot as MR, drm_reloc as R
from drm import cdrm_decode, sections_with_data
L=MR.libs(); PM=L['PM']; DM=L['DM']
T='/path/to/trudlcport/work/baseline/B8/mods/'
def load(drm,mid):
    raw=cdrm_decode(open(T+drm,'rb').read(),'le'); _,secs=sections_with_data(raw,'le')
    s=[s for s in secs if s['type']==10 and s['id']==mid][0]; return s['data'],s['reloc']
def params(d,r,e='<'):
    n=struct.unpack_from(e+'I',d,0x58)[0]; rel=R.parse(r,'le' if e=='<' else 'be')
    o=dict(rel.internal).get(0x5c)
    return n,[struct.unpack_from(e+'4f',d,o+16*i) for i in range(n)] if o is not None else None
for mid,drm in [(20263,'streamgroups/dlc_dungeon_dungeon_main.drm'),(22619,'streamgroups/dlc_dungeon_dungeon_main.drm'),(24101,'streamgroups/dlc_dungeon_dungeon_main.drm'),(21183,'streamgroups/dlc_treasureroom_treasureroom_main.drm')]:
    d,r=load(drm,mid); pt=struct.unpack_from('<4I',d,0x28)
    print('==',mid,'pt',pt,'hdr',d[:0x58].hex())
    n,p=params(d,r); print(' PC n',n)
    for i,v in enumerate(p or []): print('  p%d'%i,['%.4g'%x for x in v])
    xd,xr=DM[mid]; xn,xp=params(xd,xr,'>'); print(' Xbox n',xn,'xt',struct.unpack_from('>4I',xd,0x28))
    for i,v in enumerate(xp or []): print('  x%d'%i,['%.4g'%x for x in v])
    sib=[b for b,(bd,br) in PM.items() if struct.unpack_from('<4I',bd,0x28)[:3]==pt[:3]]
    print(' base PC mats w/ same tuple:',sib[:10])
    for b in sib[:2]:
        bd,br=PM[b]; bn,bp=params(bd,br); print('  base',b,'hdr',bd[:0x58].hex()); 
        for i,v in enumerate(bp or []): print('   b%d'%i,['%.4g'%x for x in v])
