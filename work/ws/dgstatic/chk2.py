import sys,re,os,collections,struct
sys.path.insert(0,'/path/to/trudlcport/tools')
import drm, drm_reloc as R
W='/path/to/trudlcport/work/'
# 1: names in dlc packs that collide with base-PC object names
names=[l.split(None,5) for l in open(W+'generic/dlc_names.txt')]
dl={p[5].strip().lower().split('\\')[-1] for p in names if len(p)==6}
for n in ['ma_dungeon_watersurfaces','ma_rb_chapel_gate_round','fx_rain_gutter_mex_splash_ist','dispatcher','reveal_object','watervolume','triggervolume','triggerplane','soundtriggervolume','checkpoint','small_albino_spider','giant_albino_tarantula','bat_enemy','ma_rw_artifact','ma_rw_treasure','cameraanchor_object','knight_thrall','player','lara']:
    print(n, 'in DLC packs' if n+'.drm' in dl else 'not in DLC packs')
print([x for x in dl if 'dispatcher' in x or 'watersurf' in x])
def secs(p,e):
    raw=drm.cdrm_decode(open(p,'rb').read(),e); return drm.sections_with_data(raw,e)[1]
# 2: shaders
for f in ['dlc_dungeon_dungeon_main.drm','dlc_dungeon_dungeon_sewer.drm']:
    ps=secs(W+'baseline/B8/mods/streamgroups/'+f,'le'); 
    ids=sorted(s['id'] for s in ps if s['type']==9)
    print(f,'PC t9',len(ids),'has1465-8',[i for i in ids if 1465<=i<=1468],'has975/976',[i for i in ids if i in(975,976)])
    # materials (t10) referencing shader ids via id relocs
    for s in ps:
        if s['type']==10:
            rel=R.parse(s['reloc'],'le') if s['reloc'] else None
            if rel is None: continue
            for t,o in list(rel.idref)+list(rel.idref_a):
                if t==9:
                    v=struct.unpack_from('<I',s['data'],o)[0]
                    if s['id'] in (20262,23171): print('  mat',s['id'],'off',hex(o),'-> shader',v,'in-file' if v in ids else 'NOT in this file')
