import sys; sys.path.insert(0,'work/ws/fpfloat'); sys.path.insert(0,'tools')
from explore import *
cases=[('dlc1_uo_raft_bridge_spawned.drm',21222),('dlc1_uo_bend_switches.drm',21120),('dlc1_uo_bend_switches.drm',23382),('dlc1_uo_dragon_slider.drm',21094),('dlc1_uo_dragon_slider.drm',21163),('cinstream/pdlc1_010_intro.drm',23767),('dlc1_uo_sewer_gate.drm',21105),('dlc1_uo_sewer_gate.drm',21104),('dlc1_uo_water_wheel.drm',20790)]
for name,did in cases:
    try: xs,D,prs=pairs_for(name)
    except Exception as e: print(name,'ERR',e); continue
    for x,i in prs:
        sec=D.sections[i]
        if sec.id!=did: continue
        rel=R.parse(x['reloc'],'be'); xd=x['data']
        print(name,did,'type',x['type'],'len',len(xd),'node0',A.node0(xd,rel),'word0',xd[:8].hex(),'base_content',A.base_content(x), 'xid',x['id'])
