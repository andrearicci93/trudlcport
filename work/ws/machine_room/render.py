import sys,struct,math; sys.path.insert(0,'C:/tru-port/tools'); import drm_write as DW, terrain_convert as TC
import numpy as np
from PIL import Image
S=DW.read(open('C:/tru-port/work/baseline/B275_tgflag/mods/streamgroups/dlc2_machine_room_machine_room_all.drm','rb').read(),'le').sections
OFF=np.array((-1414.8,-20123.5,-37922.1))
tris=[];sid=[]
for si,s in enumerate(S):
    if s.type!=12 or not TC.is_terrain(s.data): continue
    d=s.data; T=TC.parse(d,'<'); H=T['H']
    idx=np.frombuffer(d,dtype='<u2',count=T['nIdx'],offset=H+T['offIdx'])
    vbpos={}
    for k,(voff,_z,nv,vfi) in enumerate(T['vbs']):
        st=T['vfs'][vfi]['stride']; a=np.frombuffer(d,dtype=np.uint8,count=nv*st,offset=H+voff).reshape(nv,st)
        vbpos[k]=np.ascontiguousarray(a[:,0:12]).view('<f4').reshape(nv,3).astype(np.float32)+OFF.astype(np.float32)
    for slot,seq,L in TC.draw_lists(d,T,'<'):
        for yi,cnt,stt in L:
            P=vbpos[T['Y'][yi][1]][idx[stt:stt+cnt].reshape(-1,3)]; tris.append(P); sid+=[si]*len(P)
tris=np.concatenate(tris); sid=np.array(sid)
cam=np.array([float(v) for v in sys.argv[1].split(',')]); yaw=math.radians(float(sys.argv[2])); pitch=math.radians(float(sys.argv[3])); out=sys.argv[4]
c=tris.mean(1); keep=np.linalg.norm(c-cam,axis=1)<9000; T3=tris[keep]; SID=sid[keep]
fwd=np.array([math.cos(yaw)*math.cos(pitch),math.sin(yaw)*math.cos(pitch),math.sin(pitch)]); right=np.cross(fwd,[0,0,1]); right/=np.linalg.norm(right); up=np.cross(right,fwd)
Wd,Hd=160,90; img=np.zeros((Hd,Wd,3),np.uint8)
v0=T3[:,0];e1=T3[:,1]-v0;e2=T3[:,2]-v0; nrm=np.cross(e1,e2)
pal=np.array([[200,200,200],[0,0,0],[90,160,255],[255,200,60],[255,120,120],[120,255,120],[255,120,255],[120,255,255],[200,140,90],[150,150,255],[255,255,120],[180,80,200],[80,200,160]])
for yy in range(Hd):
    for xx in range(Wd):
        u=(xx-Wd/2)/(Wd/2)*1.0; v=-(yy-Hd/2)/(Wd/2)*1.0
        dv=fwd+u*right+v*up; dv/=np.linalg.norm(dv)
        h=np.cross(dv,e2); a=(e1*h).sum(1); ok=np.abs(a)>1e-6; f=np.where(ok,1/np.where(ok,a,1),0)
        s_=cam-v0; uu=f*(s_*h).sum(1); q=np.cross(s_,e1); vv=f*(q*dv).sum(1); t=f*(e2*q).sum(1)
        m=ok&(uu>=0)&(vv>=0)&(uu+vv<=1)&(t>1)
        if not m.any(): continue
        j=np.where(m)[0]; k=j[t[j].argmin()]
        front=(nrm[k]@dv)<0
        col=pal[SID[k]%len(pal)].astype(float)*(1.0 if front else 0.35)
        if not front: col=np.array([255,0,0])*0.6+col*0.4
        img[yy,xx]=np.clip(col*(0.5+0.5*min(1,2000/t[k])),0,255)
Image.fromarray(img).resize((640,360),Image.NEAREST).save(out); print('ok',out)
