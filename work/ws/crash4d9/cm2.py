import sys,struct
sys.path.insert(0,'/path/to/trudlcport/tools'); sys.path.insert(0,'.')
import cmpm
from cmpm import *
for r in ('streamgroups/dlc_pillory_pillorymain.drm','streamgroups/dlc_dungeonhalla_dungeonhalla_b.drm','streamgroups/dlc_dungeonhallb_dungeonhallb_a.drm','streamgroups/dlc_dungeonhallb_dungeonhallb_b.drm'):
    a=mats(W+'B8/mods/'+r); b=mats(W+'B10/mods/'+r)
    for k in a:
        if a[k].data==b[k].data and a[k].reloc==b[k].reloc: continue
        print(r,k)
        for tag,s in (('B8',a[k]),('B10',b[k])):
            es=ent(s); print(' ',tag,tuple(s.data[0x50:0x53]),[ (struct.unpack_from('<I',e,8)[0],e[0xc],e[0xd]) for e in es])
        d=[i for i in range(len(a[k].data)) if a[k].data[i]!=b[k].data[i]]
        print('  datadiff',len(a[k].data),len(b[k].data),[hex(x) for x in d[:20]])
