"""Search planar disc-like triangle components in terrain sections (type 12 w/o Mesh magic). usage: disc.py drm [sid...]"""
import sys,struct,collections
sys.path.insert(0,'/path/to/trudlcport/tools')
import numpy as np
from drm import cdrm_decode, sections_with_data
import terrain_convert as TC, drm_reloc as R
def comps(tris):
    par={}
    def f(a):
        while par.setdefault(a,a)!=a:
            par[a]=par[par[a]]; a=par[a]
        return a
    for t in tris:
        for v in t[1:]: par[f(v)]=f(t[0])
    g=collections.defaultdict(list)
    for t in tris: g[f(t[0])].append(t)
    return g.values()
def run(f,sids=None,minT=20):
    raw=cdrm_decode(open(f,'rb').read(),'le'); _,secs=sections_with_data(raw,'le')
    out=[]
    for s in secs:
        if s['type']!=12 or s['data'][0x10:0x14] in (b'hseM',b'Mesh'): continue
        if sids and s['id'] not in sids: continue
        d=s['data']; T=TC.parse(d,'<'); H=T['H']; rel=R.parse(s['reloc'],'le')
        ml=[struct.unpack_from('<I',d,o)[0] for t,o in sorted(rel.idref+rel.idref_a,key=lambda x:x[1]) if t==10]
        idx=np.frombuffer(d,'<u2',count=T['nIdx'],offset=H+T['offIdx']).astype(int)
        vbp=[]
        for vb in T['vbs']:
            st=T['vfs'][vb[3]]['stride']
            arr=np.frombuffer(d,np.uint8,count=vb[2]*st,offset=H+vb[0]).reshape(vb[2],st)
            vbp.append(arr[:,0:12].copy().view('<f4').reshape(-1,3))
        seen=set(); per=collections.defaultdict(list)
        for k,seq,es in TC.draw_lists(d,T,'<'):
            for y,n,st in es:
                if (y,st,n) in seen: continue
                seen.add((y,st,n)); Y=T['Y'][y]
                ii=idx[st:st+n].reshape(-1,3)
                for t in ii:
                    if len(set(t))==3: per[(Y[1],ml[Y[0]],Y[6],Y[8])].append(tuple(t))
        for key,tris in per.items():
            P=vbp[key[0]]
            for c in comps(tris):
                if len(c)<minT: continue
                vs=sorted({v for t in c for v in t}); X=P[vs]
                ce=X.mean(0); u,sv,vt=np.linalg.svd(X-ce,full_matrices=False)
                if sv[1]<=0: continue
                pl=sv[2]/sv[1]
                Q=(X-ce)@vt[:2].T; r=np.linalg.norm(Q,axis=1); rmax=r.max()
                area=0
                for t in c:
                    a,b,cc=P[list(t)]; area+=np.linalg.norm(np.cross(b-a,cc-a))/2
                circ=area/(np.pi*rmax**2)
                ext=(Q.max(0)-Q.min(0))
                out.append(dict(sid=s['id'],mat=key[1],atlas=(key[2],key[3]),ntri=len(c),planar=pl,circ=circ,asp=ext.min()/ext.max(),rmax=rmax,ce=ce.round(),nrm=vt[2].round(2)))
    return out
if __name__=='__main__':
    f=sys.argv[1]; sids=set(int(x) for x in sys.argv[2:]) or None
    o=run(f,sids)
    sel=[x for x in o if x['planar']<0.03 and 0.5<x['circ']<1.3 and x['asp']>0.6 and 150<x['rmax']<2500]
    sel.sort(key=lambda x:-x['ntri'])
    print(len(o),'components',len(sel),'disc-like')
    for x in sel[:40]: print({k:(round(float(v),2) if isinstance(v,(float,np.floating)) else (v.tolist() if hasattr(v,'tolist') else v)) for k,v in x.items()})
