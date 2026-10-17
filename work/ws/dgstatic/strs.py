import sys,re
sys.path.insert(0,'/path/to/trudlcport/tools')
import drm
W='/path/to/trudlcport/work/'
keys=[b'dispatcher_water',b'population is',b'birth tarantula',b'spawn first',b'planner obstacle',b'birth side',b'lowering']
import os
for p in [W+'ws/dgstatic/xbox/dlc_dispatcher.drm',W+'ws/dgstatic/xbox/dlc_dungeon.drm',W+'baseline/B8/mods/dlc_dungeon.drm',W+'baseline/B8/mods/dlc_dispatcher.drm']:
    e='be' if 'xbox' in p else 'le'
    raw=drm.cdrm_decode(open(p,'rb').read(),e); secs=drm.sections_with_data(raw,e)[1]
    print('==',p.split('work/')[-1],len(secs))
    for s in secs:
        for k in keys:
            for m in re.finditer(re.escape(k),s['data']):
                a=s['data'][max(0,m.start()-30):m.end()+60]
                print('  sec',s['i'],'type',s['type'],'id',s['id'],'off',hex(m.start()),re.sub(rb'[^ -~]',b'.',a).decode())
