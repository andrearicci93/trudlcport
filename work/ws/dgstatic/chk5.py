import sys,struct
sys.path.insert(0,'/path/to/trudlcport/tools')
import drm, drm_reloc as R
W='/path/to/trudlcport/work/'
def secs(p,e):
    raw=drm.cdrm_decode(open(p,'rb').read(),e); return drm.sections_with_data(raw,e)[1]
xs=secs(W+'ws/dgstatic/xbox/dlc_dungeon_dungeon_main.drm','be')
ids9={s['id'] for s in xs if s['type']==9}
for s in xs:
    if s['type']==10 and s['id']==20262:
        rel=R.parse(s['reloc'],'be')
        print('Xbox mat 20262 shader refs',[(hex(o),struct.unpack_from('>I',s['data'],o)[0], struct.unpack_from('>I',s['data'],o)[0] in ids9) for t,o in rel.idref if t==9])
    if s['type']==12 and s['id']==23806: print('Xbox mesh 23806 size',s['size'])
ps=secs(W+'baseline/B8/mods/streamgroups/dlc_dungeon_dungeon_main.drm','le')
for s in ps:
    if s['type']==12 and s['id']==23806: print('PC mesh size',s['size'])
# mesh: also dlc_caverns t12 20869 size
cs=secs(W+'baseline/B8/mods/dlc_caverns.drm','le')
print([ (s['id'],s['type'],s['size']) for s in cs if s['id'] in (975,976,20869) ])
