import sys,struct,os
sys.path.insert(0,'/path/to/trudlcport/tools')
import drm, drm_reloc as R
W='/path/to/trudlcport/work/'
def secs(p,e):
    raw=drm.cdrm_decode(open(p,'rb').read(),e); return drm.sections_with_data(raw,e)[1]
P=W+'baseline/B8/mods/streamgroups/'
for f,sid in [('dlc_dungeonhalla_dungeonhalla_a.drm',23244),('dlc_dungeonhalla_dungeonhalla_b.drm',23245),('dlc_dungeonhallb_dungeonhallb_a.drm',21266),('dlc_dungeonhallb_dungeonhallb_b.drm',23202)]:
    xs=secs(W+'ws/dgstatic/xbox/'+f,'be'); ps=secs(P+f,'le')
    x=[s for s in xs if s['type']==12 and s['id']==sid][0]; y=[s for s in ps if s['type']==12 and s['id']==sid][0]
    ids=set(R.parse(y['reloc'],'le').id_offsets()); idx=set(R.parse(x['reloc'],'be').id_offsets())
    a,b=x['data'],y['data']
    diff=[i for i in range(0,len(a),4) if a[i:i+4][::-1]!=b[i:i+4]]
    notid=[i for i in diff if i not in ids]
    print(f,sid,'diff words',len(diff),'of which not at idref offsets',len(notid),'idref offsets same',ids==idx, 'first non-id',[hex(i) for i in notid[:5]])
    if notid:
        i=notid[0]; print('  X',a[i:i+16].hex(),'P',b[i:i+16].hex())
print('---- neither raw nor swapped words')
for f,sid in [('dlc_dungeonhalla_dungeonhalla_a.drm',23244),('dlc_dungeonhallb_dungeonhallb_a.drm',21266)]:
    xs=secs(W+'ws/dgstatic/xbox/'+f,'be'); ps=secs(P+f,'le')
    x=[s for s in xs if s['type']==12 and s['id']==sid][0]; y=[s for s in ps if s['type']==12 and s['id']==sid][0]
    a,b=x['data'],y['data']; ids=set(R.parse(y['reloc'],'le').id_offsets())
    nn=[i for i in range(0,len(a),4) if a[i:i+4]!=b[i:i+4] and a[i:i+4][::-1]!=b[i:i+4] and i not in ids]
    sw=sum(1 for i in range(0,len(a),4) if a[i:i+4]!=b[i:i+4] and a[i:i+4][::-1]==b[i:i+4]); raw=sum(1 for i in range(0,len(a),4) if a[i:i+4]==b[i:i+4])
    print(f,'words',len(a)//4,'raw-equal',raw,'swapped',sw,'other(non-id)',len(nn),[ (hex(i),a[i:i+4].hex(),b[i:i+4].hex()) for i in nn[:4]])
