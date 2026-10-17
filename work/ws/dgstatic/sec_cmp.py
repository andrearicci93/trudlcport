import sys, os, collections
sys.path.insert(0,'/path/to/trudlcport/tools'); sys.path.insert(0,'/path/to/trudlcport/work/ws/dgstatic')
import drm
W='/path/to/trudlcport/work/'
def secs(p,e):
    raw=drm.cdrm_decode(open(p,'rb').read(),e); return drm.sections_with_data(raw,e)[1]
def summ(s):
    c=collections.Counter(x['type'] for x in s); b=collections.Counter()
    for x in s: b[x['type']]+=x['size']
    return c,b
files=sys.argv[1:]
for f in files:
    xp=W+'ws/dgstatic/xbox/'+f; pp=W+'baseline/B8/mods/'+('streamgroups/' if '_' in f.replace('dlc_','',1) and f.count('_')>=2 and 'map' not in f else '')+f
    if not os.path.exists(pp): pp=W+'baseline/B8/mods/'+f
    xs=secs(xp,'be'); ps=secs(pp,'le')
    xc,xb=summ(xs); pc,pb=summ(ps)
    print('==',f,'secs X %d PC %d'%(len(xs),len(ps)))
    for t in sorted(set(xc)|set(pc)):
        print('   type %2d  X n=%-5d bytes=%-10d | PC n=%-5d bytes=%-10d %s'%(t,xc[t],xb[t],pc[t],pb[t],'' if xc[t]==pc[t] else '<<< n differs'))
