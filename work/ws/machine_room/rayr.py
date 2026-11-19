# raggi dalla posizione di Lara contro i triangoli del terreno disegnato (tutte le sezioni terreno dello streamgroup)
import sys,struct,math; sys.path.insert(0,'C:/tru-port/tools'); import drm_write as DW, terrain_convert as TC
import numpy as np
S=DW.read(open('C:/tru-port/work/baseline/B273_typelist2/mods/streamgroups/dlc2_machine_room_machine_room_all.drm','rb').read(),'le').sections
OFF=np.array((-1414.8,-20123.5,-37922.1))
tris=[];meta=[]
for si,s in enumerate(S):
    if s.type!=12 or not TC.is_terrain(s.data): continue
    d=s.data; T=TC.parse(d,'<'); H=T['H']
    idx=np.frombuffer(d,dtype='<u2',count=T['nIdx'],offset=H+T['offIdx'])
    vbpos={}
    for k,(voff,_z,nv,vfi) in enumerate(T['vbs']):
        st=T['vfs'][vfi]['stride']; a=np.frombuffer(d,dtype=np.uint8,count=nv*st,offset=H+voff).reshape(nv,st)
        vbpos[k]=np.ascontiguousarray(a[:,0:12]).view('<f4').reshape(nv,3).astype(np.float64)+OFF
    for slot,seq,L in TC.draw_lists(d,T,'<'):
        for yi,cnt,stt in L:
            vb=T['Y'][yi][1]; ii=idx[stt:stt+cnt].reshape(-1,3); P=vbpos[vb][ii]
            tris.append(P); meta+= [(si,s.id,yi,slot,T['Y'][yi][0])]*len(P)
tris=np.concatenate(tris); print('triangoli',len(tris))
def ray(o,dv):
    o=np.array(o,float); dv=np.array(dv,float); dv/=np.linalg.norm(dv)
    v0,v1,v2=tris[:,0],tris[:,1],tris[:,2]; e1=v1-v0; e2=v2-v0
    h=np.cross(dv,e2); a=(e1*h).sum(1); ok=np.abs(a)>1e-9; f=np.where(ok,1/np.where(ok,a,1),0)
    s=o-v0; u=f*(s*h).sum(1); q=np.cross(s,e1); v=f*(q*dv).sum(1); t=f*(e2*q).sum(1)
    m=ok&(u>=0)&(v>=0)&(u+v<=1)&(t>1)
    j=np.where(m)[0]; j=j[np.argsort(t[j])][:3]
    return [(round(float(t[k])),meta[k],'fronte' if a[k]<0 else 'retro') for k in j]
O=(-2502.9,6780.4,-12850)
for ang in range(0,360,20):
    dv=(math.cos(math.radians(ang)),math.sin(math.radians(ang)),0)
    print('%3d'%ang, ray(O,dv))
