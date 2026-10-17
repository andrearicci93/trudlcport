import sys
sys.path.insert(0,'/path/to/trudlcport/tools')
import engine_walk_check as E
have=E.pc_name_set()
for n in ['ma_dungeon_watersurfaces','ma_rb_chapel_gate_round','ma_rw_artifact','ma_rw_treasure','dispatcher','watervolume','triggervolume','reveal_object','small_albino_spider','giant_albino_tarantula','checkpoint','knight_thrall','bat_enemy','soundtriggervolume','triggerplane','cameraanchor_object','tp_rw_artifact','fx_rain_gutter_mex_splash_ist']:
    print(n, E.norm(n+'.drm') in have, [h for h in have if n in h][:3])
