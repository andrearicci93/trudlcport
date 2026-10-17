import sys,re
sys.path.insert(0,'/path/to/trudlcport/tools')
import drm
W='/path/to/trudlcport/work/'
p=W+'baseline/B8/mods/dlc_dungeon.drm'
raw=drm.cdrm_decode(open(p,'rb').read(),'le'); secs=drm.sections_with_data(raw,'le')[1]
ids=[int(a) for a in sys.argv[1:]]
for s in secs:
    if s['type']==8 and s['id'] in ids:
        print('=== script',s['id'],'size',s['size'])
        out=[m.group(0).decode() for m in re.finditer(rb'[ -~]{4,}',s['data'])]
        print(' | '.join(out))
