import sys,struct,glob,os
sys.path.insert(0,'/path/to/trudlcport/tools')
from drm import cdrm_decode, sections_with_data
ids={729,830,831,832,833,834,3517,3518,3519,3520,3521,2}
T='/path/to/trudlcport/work/baseline/B11/mods/streamgroups/dlc_dungeon_dungeon_main.drm'
raw=cdrm_decode(open(T,'rb').read(),'le'); _,secs=sections_with_data(raw,'le')
print('dlc dungeon_main:')
for s in secs:
    if s['type']==5 and s['id'] in ids: print(s['id'],len(s['data']),s['data'][:0x30].hex())
