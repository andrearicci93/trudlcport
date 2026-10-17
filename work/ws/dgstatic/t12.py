import sys, os, struct, collections
sys.path.insert(0,'/path/to/trudlcport/tools')
import drm
W='/path/to/trudlcport/work/'
def secs(p,e):
    raw=drm.cdrm_decode(open(p,'rb').read(),e); return drm.sections_with_data(raw,e)[1]
f='dlc_dungeon_dungeon_main.drm'
xs=secs(W+'ws/dgstatic/xbox/'+f,'be'); ps=secs(W+'baseline/B8/mods/streamgroups/'+f,'le')
def bytype(s,t): return [x for x in s if x['type']==t]
for t in (12,10,5,9):
    a=bytype(xs,t); b=bytype(ps,t)
    ida=[x['id'] for x in a]; idb=[x['id'] for x in b]
    print('type',t,'n',len(a),len(b),'ids equal(list)',ida==idb,'ids equal(set)',set(ida)==set(idb),'id sample',ida[:4],idb[:4])
    if len(a)==len(b):
        ident=sum(1 for x,y in zip(a,b) if x['data']==y['data']); sw=sum(1 for x,y in zip(a,b) if len(x['data'])==len(y['data']) and bytes(x['data'][i^3] for i in range(len(x['data'])))==y['data']) if t==12 else 0
        sz=sum(1 for x,y in zip(a,b) if x['size']==y['size'])
        print('   bytes identical %d, size equal %d, (t12) 32-bit-swapped equal %d'%(ident,sz,sw))
print('--- t12 permutation test over all 13 streamgroups')
P=W+'baseline/B8/mods/streamgroups/'
tot=0; perm=0; other=[]
for f in sorted(os.listdir(P)):
    if not f.startswith(('dlc_dungeon','dlc_treasure','dlc_watertunnel')): continue
    xs=secs(W+'ws/dgstatic/xbox/'+f,'be'); ps=secs(P+f,'le')
    for x,y in zip([s for s in xs if s['type']==12],[s for s in ps if s['type']==12]):
        tot+=1
        if sorted(x['data'])==sorted(y['data']): perm+=1
        else: other.append((f,x['id'],x['size']))
        
print(tot,perm,'byte-multiset equal; non-equal:',other[:10])
