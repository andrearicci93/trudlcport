import sys,struct,collections
sys.path.insert(0,'/path/to/trudlcport/tools')
from drm import cdrm_decode, sections_with_data
import terrain_convert as TC, drm_reloc as R
f='/path/to/trudlcport/work/mods_dlc1_rc/streamgroups/dlc_water_wheel_waterwheel_main.drm'
raw=cdrm_decode(open(f,'rb').read(),'le'); _,secs=sections_with_data(raw,'le')
for s in secs:
    if s['id'] not in (24024,24026): continue
    d=s['data']; T=TC.parse(d,'<'); print(s['id'],{k:v for k,v in T.items() if k not in('vfs','vbs','Y')})
    for i,v in enumerate(T['vfs']): print(' vf',i,v['stride'],[(hex(a),b,hex(c)) for a,b,c,_ in v['elems']])
    for i,v in enumerate(T['vbs']): print(' vb',i,v)
    dl=TC.draw_lists(d,T,'<')
    cnt=collections.Counter()
    for k,seq,es in dl:
        for y,n,st in es: cnt[y]+=n
    rel=R.parse(s['reloc'],'le')
    ids=[struct.unpack_from('<I',d,o)[0] for t,o in sorted(rel.idref+rel.idref_a,key=lambda x:x[1]) if t==10]
    print(' nY',T['nY'],'ids mats',len(ids))
    for y,n in sorted(cnt.items()): print('  Y',y,T['Y'][y][:2],'idx',n)

import numpy as np
s=[x for x in secs if x['id']==24024][0]; d=s['data']; T=TC.parse(d,'<'); H=T['H']
dl=TC.draw_lists(d,T,'<')
idx=np.frombuffer(d,'<u2',count=T['nIdx'],offset=H+T['offIdx'])
for target in (83,80,81,82,6,20,13):
    for k,seq,es in dl:
        for y,n,st in es:
            if y==target:
                vb=T['vbs'][T['Y'][y][1]]; vf=T['vfs'][vb[3]]
                ii=idx[st:st+n]
                print('Y',y,'mat idx',T['Y'][y][0],'vb',T['Y'][y][1],'n',n,'start',st,'node',k,'vert idx',ii[:6])
                for v in sorted(set(ii.tolist()))[:6]:
                    a=H+vb[0]+v*vf['stride']
                    pos=struct.unpack_from('<3f',d,a); uv=struct.unpack_from('<2h',d,a+20)
                    print('    v',v,[round(x,1) for x in pos],uv)

print('=== mat 25 (20670)')
import numpy as np
allv=set()
for k,seq,es in dl:
    for y,n,st in es:
        if T['Y'][y][0]==25:
            vb=T['vbs'][T['Y'][y][1]]; vf=T['vfs'][vb[3]]
            ii=idx[st:st+n]; allv|={(T['Y'][y][1],v) for v in ii.tolist()}
            print(' Y',y,'node',k,'n',n,'vf',vb[3],[hex(e[0]) for e in vf['elems']])
P=[];C=[]
for b,v in sorted(allv):
    vb=T['vbs'][b]; vf=T['vfs'][vb[3]]; a=H+vb[0]+v*vf['stride']
    P.append(struct.unpack_from('<3f',d,a)); 
    col=[e for e in vf['elems'] if e[2]==4]
    C.append(d[a+col[0][1]:a+col[0][1]+4].hex() if col else None)
P=np.array(P); print('bbox',P.min(0),P.max(0),len(P)); print(collections.Counter(C).most_common(12))
