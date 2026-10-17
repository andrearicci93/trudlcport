import sys,struct,collections
sys.path.insert(0,'/path/to/trudlcport/tools')
from drm import cdrm_decode, sections_with_data
import terrain_convert as TC, drm_reloc as R
import numpy as np
f,X,Y,Z=sys.argv[1],*map(float,sys.argv[2:5])
raw=cdrm_decode(open(f,'rb').read(),'le'); _,secs=sections_with_data(raw,'le')
cnt=collections.Counter(); ex={}; allp=[]
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
            mi=T['Y'][y][0]; vb=T['vbs'][T['Y'][y][1]]; vf=T['vfs'][vb[3]]
            for v in set(idx[st:st+n].tolist()):
                p=struct.unpack_from('<3f',d,H+vb[0]+v*vf['stride'])
                allp.append(p)
                if abs(p[0]-X)<150 and abs(p[1]-Y)<150 and -400<p[2]-Z<30:
                    m=ids[mi] if mi<len(ids) else None; cnt[(s['id'],m)]+=1; ex.setdefault((s['id'],m),p)
print(cnt.most_common(15)); print({k:tuple(round(x) for x in v) for k,v in ex.items()})

a=np.array(allp); print('bbox',a.min(0).round(),a.max(0).round(),len(a))
