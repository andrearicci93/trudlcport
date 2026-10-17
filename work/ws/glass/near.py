import sys,struct,collections
sys.path.insert(0,'/path/to/trudlcport/tools')
import numpy as np
from drm import cdrm_decode, sections_with_data
import terrain_convert as TC, drm_reloc as R
f,sid=sys.argv[1],int(sys.argv[2]); c=np.array([float(x) for x in sys.argv[3:6]]); rad=float(sys.argv[6])
raw=cdrm_decode(open(f,'rb').read(),'le'); _,secs=sections_with_data(raw,'le')
for s in secs:
    if s['id']!=sid: continue
    d=s['data']; T=TC.parse(d,'<'); H=T['H']; rel=R.parse(s['reloc'],'le')
    ml=[struct.unpack_from('<I',d,o)[0] for t,o in sorted(rel.idref+rel.idref_a,key=lambda x:x[1]) if t==10]
    idx=np.frombuffer(d,'<u2',count=T['nIdx'],offset=H+T['offIdx']).astype(int)
    seen=set(); res=collections.defaultdict(lambda:[0,None,None])
    for k,seq,es in TC.draw_lists(d,T,'<'):
        for y,n,st in es:
            if (y,st,n) in seen: continue
            seen.add((y,st,n)); Y=T['Y'][y]
            vb=T['vbs'][Y[1]]; stv=T['vfs'][vb[3]]['stride']
            arr=np.frombuffer(d,np.uint8,count=vb[2]*stv,offset=H+vb[0]).reshape(vb[2],stv)
            pos=arr[:,0:12].copy().view('<f4').reshape(-1,3)
            ii=idx[st:st+n]; P=pos[ii]
            m=np.linalg.norm(P-c,axis=1)<rad
            if m.sum()==0: continue
            r=res[(ml[Y[0]],y,Y[1],Y[6],Y[8])]
            r[0]+=m.sum()//3
            lo,hi=P[m].min(0),P[m].max(0)
            r[1]=lo if r[1] is None else np.minimum(r[1],lo); r[2]=hi if r[2] is None else np.maximum(r[2],hi)
    for k,v in sorted(res.items(),key=lambda x:-x[1][0]): print('mat',k[0],'Y',k[1],'vb',k[2],'atlas',k[3:],'tris~',v[0],v[1].round().tolist(),v[2].round().tolist())
