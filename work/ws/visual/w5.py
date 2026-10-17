import sys,struct
sys.path.insert(0,'/path/to/trudlcport/tools')
from drm import cdrm_decode, sections_with_data
import drm_reloc as R
from mesh_tr8 import Mesh, SEM, H
T='/path/to/trudlcport/work/baseline/B11/mods/streamgroups/'
for f in ('dlc_dungeon_dungeon_main.drm','dlc_dungeon_dungeon_to_watertunnel.drm'):
    raw=cdrm_decode(open(T+f,'rb').read(),'le'); _,secs=sections_with_data(raw,'le')
    for s in secs:
        if s['type']!=12: continue
        rel=R.parse(s['reloc'],'le')
        ms=[struct.unpack_from('<I',s['data'],o)[0] for t,o in rel.idref+rel.idref_a if t==10]
        if 20263 in ms or 22619 in ms:
            print(f,s['id'],len(s['data']),ms,s['data'][:0x30].hex()); continue
            print(f,s['id'],len(s['data']),'mats',ms,'nbatch',len(m.meshes),'hdr',s['data'][:0x40].hex())
            for b in m.meshes:
                vf=b['vf']; print('   vf',vf and vf['stride'], vf and [hex(e[0]) for e in vf['elems']], {k:v for k,v in b.items() if k not in('vf',)})
