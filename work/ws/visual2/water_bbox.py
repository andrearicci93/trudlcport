import sys,struct,collections
sys.path.insert(0,'/path/to/trudlcport/tools')
from drm import cdrm_decode, sections_with_data
import terrain_convert as TC, drm_reloc as R
import numpy as np
f=sys.argv[1]
raw=cdrm_decode(open(f,'rb').read(),'le'); _,secs=sections_with_data(raw,'le')
print([(s['id'],s['type'],len(s['data'])) for s in secs if s['type'] in (12,10)][:40])
for s in secs:
    if s['type']!=12: continue
    d=s['data']
    try: T=TC.parse(d,'<')
    except Exception as e: continue
    rel=R.parse(s['reloc'],'le')
    ids=[struct.unpack_from('<I',d,o)[0] for t,o in sorted(rel.idref+rel.idref_a,key=lambda x:x[1]) if t==10]
    print('terrain',s['id'],'nY',T['nY'],'mats',ids[:60])
    dl=TC.draw_lists(d,T,'<'); H=T['H']
    idx=np.frombuffer(d,'<u2',count=T['nIdx'],offset=H+T['offIdx'])
    for target in (20263,22619):
        if target not in ids: continue
        pts=[]
        for k,seq,es in dl:
            for y,n,st in es:
                mi=T['Y'][y][0]
                if mi<len(ids) and ids[mi]==target:
                    vb=T['vbs'][T['Y'][y][1]]; vf=T['vfs'][vb[3]]
                    for v in set(idx[st:st+n].tolist()):
                        pts.append(struct.unpack_from('<3f',d,H+vb[0]+v*vf['stride']))
        if pts:
            a=np.array(pts); print(' water',target,len(pts),'min',a.min(0).round(0),'max',a.max(0).round(0),'mean',a.mean(0).round(0))
print('--- hist z per mat')
for s in secs:
    if s['type']!=12: continue
    d=s['data']
    try: T=TC.parse(d,'<')
    except Exception: continue
    rel=R.parse(s['reloc'],'le')
    ids=[struct.unpack_from('<I',d,o)[0] for t,o in sorted(rel.idref+rel.idref_a,key=lambda x:x[1]) if t==10]
    dl=TC.draw_lists(d,T,'<'); H=T['H']
    idx=np.frombuffer(d,'<u2',count=T['nIdx'],offset=H+T['offIdx'])
    for target in (20263,22619):
        for k,seq,es in dl:
            for y,n,st in es:
                mi=T['Y'][y][0]
                if mi<len(ids) and ids[mi]==target:
                    vb=T['vbs'][T['Y'][y][1]]; vf=T['vfs'][vb[3]]
                    P=np.array([struct.unpack_from('<3f',d,H+vb[0]+v*vf['stride']) for v in set(idx[st:st+n].tolist())])
                    print(s['id'],target,'node',k,'Y',y,'nverts',len(P),'x',P[:,0].min().round(),P[:,0].max().round(),'y',P[:,1].min().round(),P[:,1].max().round(),'z',P[:,2].min().round(),P[:,2].max().round())
print('--- flat triangles (horizontal) per z level')
flat=collections.defaultdict(float); bb={}
for s in secs:
    if s['type']!=12: continue
    d=s['data']
    try: T=TC.parse(d,'<')
    except Exception: continue
    rel=R.parse(s['reloc'],'le')
    ids=[struct.unpack_from('<I',d,o)[0] for t,o in sorted(rel.idref+rel.idref_a,key=lambda x:x[1]) if t==10]
    dl=TC.draw_lists(d,T,'<'); H=T['H']
    idx=np.frombuffer(d,'<u2',count=T['nIdx'],offset=H+T['offIdx'])
    for k,seq,es in dl:
        for y,n,st in es:
            mi=T['Y'][y][0]
            if mi>=len(ids) or ids[mi] not in (20263,22619): continue
            vb=T['vbs'][T['Y'][y][1]]; vf=T['vfs'][vb[3]]
            ii=idx[st:st+n]
            tri=[ii[i:i+3] for i in range(0,len(ii)-2,3)]
            for a,b,c in tri:
                p=[np.array(struct.unpack_from('<3f',d,H+vb[0]+int(v)*vf['stride'])) for v in (a,b,c)]
                if max(abs(p[0][2]-p[1][2]),abs(p[0][2]-p[2][2]))<2:
                    ar=abs(np.cross(p[1]-p[0],p[2]-p[0])[2])/2; zl=round(p[0][2]/20)*20
                    flat[(ids[mi],zl)]+=ar
                    q=np.array(p); b0=bb.setdefault((ids[mi],zl),[q.min(0),q.max(0)]); b0[0]=np.minimum(b0[0],q.min(0)); b0[1]=np.maximum(b0[1],q.max(0))
for k,v in sorted(flat.items(),key=lambda kv:-kv[1])[:15]: print(k,'area m2',round(v/1e4,1),'bbox',bb[k][0].round(),bb[k][1].round())
