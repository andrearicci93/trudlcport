"""Gate offline con TEXEL REALI (colore medio delle texture) per i materiali trapiantati: Xbox (traduzione, texture Xbox vergini)
contro lib B84 e lib B86 (texture PC convertite, formato PC reale: DXN -> DXT5 R=x,G=255,B=0,A=y). Luci spente.
Uso: tools/venv/bin/python -I work/ws/codefirst/real_tex_gate.py [MAT ...]   (default: i 6 materiali di dlc_caverns_hall)"""
import sys,os,json,io,contextlib
sys.path.insert(0,'/path/to/trudlcport/work/ws/codefirst')
with contextlib.redirect_stdout(io.StringIO()):
    import hall_diag as H
    import tex_means as TM
import numpy as np
sys.path.insert(0,'/path/to/trudlcport/work/ws/contratti')
import f14_slotmap as F
F9,F10,F12,C=F.F9,F.F10,F.F12,F.C
sm3asm,sm3vm,xenos2sm3,libs,XL=F.sm3asm,F.sm3vm,F.xenos2sm3,F.libs,F.XL
T='/path/to/trudlcport/'
CT=json.load(open(T+'work/ws/contratti/out/contracts.json'))['materials']
_mean={}
def pc_mean(tid):
    if tid in _mean: return _mean[tid]
    ph,src=H.ptex(tid)
    if ph is None: _mean[tid]=None; return None
    if src=='hall': sec=[s for s in H._pcdrm['dlc_caverns_hall.drm'] if s['type']==5 and s['id']==tid][0]['data']
    else: sec=H.sec_from('pc',tid,'le')
    m,k=TM.mean(sec)
    if m is None: _mean[tid]=('cube',None,ph); return _mean[tid]
    if len(m)==3: m=np.append(m,255.0)
    _mean[tid]=(k,np.array(m,float)/255.0,ph); return _mean[tid]
def xbox_texel(row):
    """colore medio che l'Xbox restituisce al fetch: DXN -> (x,y,0,1) con x=R, y=A della versione PC (conversione lossless dei 2 canali)."""
    pm=pc_mean(row['pc_tex'])
    xh,_=H.xtex(row['xbox_tex'])
    if pm is None or pm[0]=='cube': return np.array([.5,.5,.5,1.])
    m=pm[1]
    if xh and xh['fmtname']=='DXN': return np.array([m[0],m[3],0.,1.])
    if xh and xh['fmtname']=='DXT1': return np.array([m[0],m[1],m[2],1.])
    return m.copy()
def pc_texel(row):
    pm=pc_mean(row['pc_tex'])
    if pm is None or pm[0]=='cube': return np.array([.5,.5,.5,1.])
    return pm[1].copy()
def const_tex(byreg):
    def f(smp,coords,mode):
        v=byreg.get(smp,np.array([.5,.5,.5,1.]))
        return np.tile(v.astype(np.float32),(coords.shape[0],1))
    return f
def colors(prog_pc,xblob,XPm,xopts,xmap,pmap,seed=F.SEED):
    pct=[]; K=F9.Consts(pct); sh=XL.parse(xblob); bn=F9.bool_names(sh); bools={i:0 for i in bn}
    o=dict(xopts or {}); o['noopt']=True
    t=xenos2sm3.translate(xblob,K.fn,bools=bools,samp=lambda n,c:c,opts=o); progX=sm3asm.parse_text(t.text)
    eX=F9.Env(seed,XPm); eP=F9.Env(seed,XPm)
    eX.tex=const_tex(xmap); eP.tex=const_tex(pmap)
    a=eP.run(prog_pc,F9.body(prog_pc),eP.state0(prog_pc),{}); b=eX.run(progX,F9.body(progX),eX.state0(progX),{})
    ca,cb=a[0].get((sm3asm.RT_COLOROUT,0)),b[0].get((sm3asm.RT_COLOROUT,0))
    return ca,cb
def lib_bcs(tree,rel,lib):
    sec={(s.type,s.id):s for s in tree[rel].sections}[(9,lib)]
    f=C.frame_lib(sec.data); return {k:f['entries'][o]['bc'] for k,o in enumerate(f['slots']) if o!=0xFFFFFFFF}
if __name__=='__main__':
    mats=sys.argv[1:] or H.hall
    t84=C.read_tree(T+'work/baseline/B84/mods'); t86=C.read_tree(T+'work/baseline/B86_contratti/mods')
    plan=F.plan_by_material(); lines=[]
    for mid in mats:
        mid=str(mid); v=CT[mid]; rows=v['sampler_map']; m=plan[int(mid)]
        rel=[r for r in v['drms'] if r=='dlc_caverns_hall.drm'][0] if 'dlc_caverns_hall.drm' in v['drms'] else v['drms'][0]
        mo=F12.material_opts(int(mid)); XPm=F10.params(F10.f9_common._Sec(*libs()['DM'][int(mid)]),'be')
        xmap={r['xbox_reg']:xbox_texel(r) for r in rows}; pmap={r['pc_slot']:pc_texel(r) for r in rows}
        D=libs()['D']; b84=lib_bcs(t84,rel,v['lib']); b86=lib_bcs(t86,rel,v['lib'])
        lines.append(f"\n=== materiale {mid} lib {v['lib']} ({rel})")
        for k in sorted(b86):
            xblob=D[v['dlc_lib']]['entries'][D[v['dlc_lib']]['slots'][k&1]]['blob']
            res={}
            for name,bcs in (('B84',b84),('B86',b86)):
                ca,cb=colors(sm3asm.decode(bcs[k]),xblob,XPm,mo,xmap,pmap)
                res[name]=ca; res['X']=cb
            X=res['X']
            def mm(c): return None if c is None else np.round(c[:,:3].mean(0),3)
            def err(c): return None if c is None or X is None else round(float(np.abs(c[:,:3]-X[:,:3]).mean()),4)
            lines.append(f"  variante {k}: colore medio RGB  Xbox={mm(X)}  B84={mm(res['B84'])}  B86={mm(res['B86'])}   |err| B84={err(res['B84'])} B86={err(res['B86'])}")
    open(T+'work/ws/codefirst/real_tex_gate.txt','w').write('\n'.join(lines)); print('\n'.join(lines))
