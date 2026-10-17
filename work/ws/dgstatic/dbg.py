import sys,struct,collections
sys.path.insert(0,'/path/to/trudlcport/tools')
import drm, drm_reloc as R
W='/path/to/trudlcport/work/'
def secs(p,e):
    raw=drm.cdrm_decode(open(p,'rb').read(),e); return drm.sections_with_data(raw,e)[1]
xs=secs(W+'ws/dgstatic/xbox/dlc_dungeon_dungeon_main.drm','be')
for x in xs:
    if x['type']==7: print(x['i'],x['id'],x['size'],R.parse(x['reloc'],'be') if x['reloc'] else None)
xs=secs(W+'ws/dgstatic/xbox/dlc_dungeon.drm','be')
c=collections.Counter((x['type'],x['size']) for x in xs if x['type']==7)
print(sorted(c.items(),key=lambda t:-t[1])[:15])
for x in xs:
    if x['id'] in (23793,23794,23795,23796): print(x['i'],x['type'],x['id'],x['size'])
