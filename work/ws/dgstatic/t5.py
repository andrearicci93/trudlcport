import sys, os, struct, collections
sys.path.insert(0,'/path/to/trudlcport/tools')
import drm
W='/path/to/trudlcport/work/'
def secs(p,e):
    raw=drm.cdrm_decode(open(p,'rb').read(),e); return drm.sections_with_data(raw,e)[1]
f='dlc_dungeon_dungeon_main.drm'
xs=secs(W+'ws/dgstatic/xbox/'+f,'be'); ps=secs(W+'baseline/B8/mods/streamgroups/'+f,'le')
for t in (5,9):
    a=[s['id'] for s in xs if s['type']==t]; b=[s['id'] for s in ps if s['type']==t]
    print('t',t,'n',len(a),len(b),'only X',sorted(set(a)-set(b))[:20],len(set(a)-set(b)),'only PC',sorted(set(b)-set(a))[:20],len(set(b)-set(a)))
    # sizes of paired
    if t==5:
        d=collections.Counter()
        for x,y in zip([s for s in xs if s['type']==5],[s for s in ps if s['type']==5]):
            d[(x['id']==y['id'])]+=1
        print(d)
