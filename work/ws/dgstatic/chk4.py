import sys,os,struct,collections
sys.path.insert(0,'/path/to/trudlcport/tools')
import drm, drm_reloc as R
W='/path/to/trudlcport/work/'; B=W+'baseline/B8/mods/'
def users(p,mid):
    raw=drm.cdrm_decode(open(p,'rb').read(),'le'); secs=drm.sections_with_data(raw,'le')[1]
    out=collections.Counter()
    for s in secs:
        if not s['reloc']: continue
        try: rel=R.parse(s['reloc'],'le')
        except Exception: continue
        for t,o in list(rel.idref)+list(rel.idref_a):
            if t==10 and struct.unpack_from('<I',s['data'],o)[0]==mid: out[(s['type'],s['id'])]+=1
    return out
for f in ['streamgroups/dlc_dungeon_dungeon_main.drm','streamgroups/dlc_dungeon_dungeon_sewer.drm','streamgroups/dlc_dungeon_dungeon_to_watertunnel.drm','streamgroups/dlc_watertunnel_watertunnel_main.drm','streamgroups/dlc_treasureroom_treasureroom_main.drm','streamgroups/dlc_dungeonhallb_dungeonhallb_a.drm','dlc_dungeon.drm','dlc_caverns.drm']:
    for m in (20262,):
        print(f,m,dict(users(B+f,m)))
# which sections of mat 20262 materials exist per file
