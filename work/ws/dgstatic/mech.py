import sys
sys.path.insert(0,'/path/to/trudlcport/tools'); sys.path.insert(0,'/path/to/trudlcport/work/ws/dgstatic')
from intros_cmp import *
pi,_,_=intros(W+'baseline/B8/mods/dlc_dungeon.drm','le')
for uid,o,f,off in pi:
    n=PO.get(o)
    if n in ('player','dlc1_uo_dragon_slider','dlc1_uo_guillotine','dlc1_uo_pillar_of_doom_a','dlc1_uo_pillar_of_doom_b','dlc1_uo_dungeon_final_gate','dlc1_uo_chapel_gate_round_b','dlc1_uo_goo_pit_gate','dlc1_uo_goo_pit_lever','watervolume','ma_dungeon_watersurfaces','ma_rb_chapel_gate_round') or (n and 'grapple' in n):
        print(n,uid,[round(x) for x in f[:3]])
