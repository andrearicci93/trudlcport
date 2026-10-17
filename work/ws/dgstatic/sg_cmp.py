import sys, os, collections
sys.path.insert(0,'/path/to/trudlcport/tools')
import drm
W='/path/to/trudlcport/work/'
def secs(p,e):
    raw=drm.cdrm_decode(open(p,'rb').read(),e); return drm.sections_with_data(raw,e)[1]
X=W+'ws/dgstatic/xbox/'; P=W+'baseline/B8/mods/streamgroups/'
for f in sorted(os.listdir(P)):
    if not f.startswith(('dlc_dungeon','dlc_treasure','dlc_watertunnel')): continue
    xs=secs(X+f,'be'); ps=secs(P+f,'le')
    xc=collections.Counter(s['type'] for s in xs); pc=collections.Counter(s['type'] for s in ps)
    xb=collections.Counter(); pb=collections.Counter()
    for s in xs: xb[s['type']]+=s['size']
    for s in ps: pb[s['type']]+=s['size']
    # id match
    xi=collections.Counter((s['type'],s['id']) for s in xs); pi=collections.Counter((s['type'],s['id']) for s in ps)
    print('==',f,'X %d secs PC %d secs; (type,id) only-X %d only-PC %d'%(len(xs),len(ps),sum((xi-pi).values()),sum((pi-xi).values())))
    for t in sorted(set(xc)|set(pc)):
        print('   t%-2d X n=%-5d %-9d | PC n=%-5d %-9d %s'%(t,xc[t],xb[t],pc[t],pb[t],'' if xc[t]==pc[t] else '<<< DIFF'))
