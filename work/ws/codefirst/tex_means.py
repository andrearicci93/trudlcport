"""Media RGB(A) del mip 0 delle texture PC (DXT1/DXT5/A8R8G8B8) coinvolte nei 6 materiali. Uso: python -I tex_means.py"""
import sys,struct,numpy as np
sys.path.insert(0,'/path/to/trudlcport/work/ws/codefirst'); sys.path.insert(0,'/path/to/trudlcport/tools')
import hall_diag as H
from tex_convert import parse_pc
def c565(v):
    r=((v>>11)&31)*255/31; g=((v>>5)&63)*255/63; b=(v&31)*255/31; return np.stack([r,g,b],-1)
def dxt_color(blk,dxt1):
    c0=blk[:,0].astype(np.uint16)|(blk[:,1].astype(np.uint16)<<8); c1=blk[:,2].astype(np.uint16)|(blk[:,3].astype(np.uint16)<<8)
    p0=c565(c0); p1=c565(c1)
    if dxt1: four=(c0>c1)[:,None]
    else: four=np.ones((len(blk),1),bool)
    p2=np.where(four,(2*p0+p1)/3,(p0+p1)/2); p3=np.where(four,(p0+2*p1)/3,np.zeros_like(p0))
    pal=np.stack([p0,p1,p2,p3],1)  # n,4,3
    idx=blk[:,4:8].astype(np.uint32); bits=idx[:,0]|(idx[:,1]<<8)|(idx[:,2]<<16)|(idx[:,3]<<24)
    sel=np.stack([(bits>>(2*k))&3 for k in range(16)],1)
    px=np.take_along_axis(pal,sel[:,:,None].repeat(3,2),1)   # n,16,3
    alpha=np.where(four|True,255,255)
    return px,(c0<=c1)&dxt1,sel
def mean(pc_sec):
    h=parse_pc(pc_sec); d=pc_sec[24:]; w,hh=h['w'],h['h']; f=h['fmt']
    if h['flags']&0x8000: return None,'cubo'
    nb=max(1,w//4)*max(1,hh//4)
    if f==0x31545844:
        blk=np.frombuffer(d[:nb*8],np.uint8).reshape(nb,8); px,tr,sel=dxt_color(blk,True)
        m=px.reshape(-1,3).mean(0); return m,'DXT1'
    if f==0x35545844:
        blk=np.frombuffer(d[:nb*16],np.uint8).reshape(nb,16); px,_,_=dxt_color(blk[:,8:],False)
        a0=blk[:,0].astype(float);a1=blk[:,1].astype(float)
        # media alfa approssimata con i due estremi (basta per capire cutout)
        return np.append(px.reshape(-1,3).mean(0),(a0.mean()+a1.mean())/2),'DXT5(rgb,alfa~)'
    if f==0x15:
        b=np.frombuffer(d[:w*hh*4],np.uint8).reshape(-1,4); return b[:,[2,1,0]].mean(0),'BGRA'
    return None,hex(f)
if __name__=='__main__':
    seen={}
    for mid in H.hall:
        for r in H.C[mid]['sampler_map']:
            t=r['pc_tex']
            if t in seen: continue
            ph,src=H.ptex(t)
            if ph is None: seen[t]=('?',None); continue
            # recupera i byte
            if src=='hall':
                sec=[s for s in H._pcdrm['dlc_caverns_hall.drm'] if s['type']==5 and s['id']==t][0]['data']
            else: sec=H.sec_from('pc',t,'le')
            seen[t]=mean(sec)[::-1]
    for t,(k,m) in sorted(seen.items()): print(t,k,None if m is None else np.round(m,0))
