"""Come match_blocks (f9_transplant) ma enumera TUTTE le mappe ingressi verificate (>=0.99) fino a cap: misura le simmetrie del blocco."""
import sys
S4='/path/to/trudlcport/work/ws/shader4'; sys.path.insert(0,S4)
from f9_transplant import *
import f9_transplant as F

def verify_b(pA,a0,a1,inA,outA,pB,b0,b1,inB,outB,imap,omap,env,bools=None):
    rng=np.random.RandomState(9); vals={i:rng.uniform(0,1,env.N).astype(np.float32) for i in inB}
    sA,cA=inject(env.state0(pA),[],0,consts=env.consts); sB,cB=inject(env.state0(pB),[],0,consts=env.consts)
    for ia in inA:
        ib=next((k for k,v in imap.items() if v==ia),None)
        v=vals[ib] if ib is not None else rng.uniform(0,1,env.N).astype(np.float32)
        sA,cA=inject(sA,[ia],v,consts=cA)
    for ib in inB: sB,cB=inject(sB,[ib],vals[ib],consts=cB)
    rA=run_state(pA,body(pA)[a0:a1],sA,cA,env.tex,env.N,bools)[0]; rB=run_state(pB,body(pB)[b0:b1],sB,cB,env.tex,env.N,bools)[0]
    ok=np.ones(env.N,bool)
    for ob,oa in omap.items():
        ok&=np.isclose(rA.get((0,oa[0]),np.zeros((env.N,4)))[:,oa[1]],rB.get((0,ob[0]),np.zeros((env.N,4)))[:,ob[1]],**TOL)
    return float(ok.mean())


def match_all(pA,a0,a1,inA,outA,pB,b0,b1,inB,outB,env,cap=200,max_try=20000,bools=None):
    fA,baseA=fingerprints(pA,a0,a1,inA,outA,env,bools); fB,baseB=fingerprints(pB,b0,b1,inB,outB,env,bools)
    def dset(f,o): return [v for v in (f[i][o] for i in f) if np.abs(v).max()>1e-6]
    def same_multiset(da,db):
        if len(da)!=len(db): return False
        used=set()
        for x in db:
            k=next((k for k,y in enumerate(da) if k not in used and np.allclose(x,y,**TOL)),None)
            if k is None: return False
            used.add(k)
        return True
    ocand={ob:[oa for oa in outA if np.allclose(baseA[oa],baseB[ob],**TOL) and same_multiset(dset(fA,oa),dset(fB,ob))] for ob in outB}
    if any(not v for v in ocand.values()): return []
    obs=list(outB); sols=[]; tries=[0]
    def omaps(k,cur):
        if k==len(obs): yield dict(cur); return
        for oa in ocand[obs[k]]:
            if oa in cur.values(): continue
            cur[obs[k]]=oa; yield from omaps(k+1,cur); del cur[obs[k]]
    for om in omaps(0,{}):
        icand={}
        for ib in inB:
            infl=any(np.abs(fB[ib][o]).max()>1e-6 for o in outB); kind=len(ib)
            if infl: icand[ib]=[ia for ia in inA if len(ia)==kind and all(np.allclose(fA[ia][om[o]],fB[ib][o],**TOL) for o in outB)]
            else: icand[ib]=[ia for ia in inA if len(ia)==kind and all(np.abs(fA[ia][om[o]]).max()<=1e-6 for o in outB)]
        if any(not v for v in icand.values()): continue
        ibs=sorted(inB,key=lambda i:len(icand[i]))
        def imaps(k,cur):
            if k==len(ibs): yield dict(cur); return
            for ia in icand[ibs[k]]:
                if ia in cur.values(): continue
                cur[ibs[k]]=ia; yield from imaps(k+1,cur); del cur[ibs[k]]
        for im in imaps(0,{}):
            tries[0]+=1
            if verify_b(pA,a0,a1,inA,outA,pB,b0,b1,inB,outB,im,om,env,bools)>=0.99:
                sols.append((im,om))
                if len(sols)>=cap: return sols
            if tries[0]>=max_try: return sols
    return sols

if __name__=='__main__':
    a,b=int(sys.argv[1]),int(sys.argv[2])
    pA,a0,a1,inA,outA=xblock_info('X',a,0); pB,b0,b1,inB,outB=xblock_info('X',b,0)
    env=Env(2); sols=match_all(pA,a0,a1,inA,outA,pB,b0,b1,inB,outB,env)
    print('soluzioni verificate',len(sols))
    mp=lambda im:{k:v for k,v in im.items() if len(k)==3}
    base=mp(sols[0][0]) if sols else {}
    for im,om in sols[:12]:
        d={k:(base[k],v) for k,v in mp(im).items() if base.get(k)!=v}
        print('  differenze MP rispetto alla prima:',{('c%d.%s'%(k[1],'xyzw'[k[2]])):('c%d.%s'%(v[1],'xyzw'[v[2]])) for k,(b_,v) in d.items()})
