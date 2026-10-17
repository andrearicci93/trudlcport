"""Esperimento Regime A (offline, nessuna scrittura in work/ws/shader4 ne' nelle baseline).
Replica build_phase di f12_build_all con un f9_transplant PATCHATO A RUNTIME:
  V0  = originale (controllo: deve riprodurre 35 costruiti / 28 esclusi di f12_report.md)
  V1  = MaterialParams del blocco PC: se la stessa lane (r,c) e' letta dal blocco del gemello Xbox Xs, il ponte e' l'IDENTITA' del layout
        (regola da codice: Xbox e PC condividono il layout MaterialParams dei materiali illuminati) invece del match per valore.
Uso: tools/venv/bin/python -I work/ws/codefirst/regime_a_exp.py V0|V1      -> out_regimeA/<V>.json + <V>.md"""
import sys,os,json,types,collections,struct,time,traceback
S4='/path/to/trudlcport/work/ws/shader4'; ROOT='/path/to/trudlcport'
OUTA=ROOT+'/work/ws/codefirst/out_regimeA'; os.makedirs(OUTA,exist_ok=True)
sys.path.insert(0,S4); sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
V=sys.argv[1] if len(sys.argv)>1 else 'V0'
src=open(S4+'/f9_transplant.py').read()
MPLOG=[]
DBG=[]
if V=='DBG':
    c="        if len(cands) != 1: raise Fail('MaterialParams c%d.%s del blocco PC: %d corrispondenti nel ponte' % (r, 'xyzw'[c], len(cands)))\n"
    assert src.count(c)==1
    src=src.replace(c,"        if len(cands) != 1: DBG_.append(dict(rc=(r,c),ms=sorted(ms),mpd=sorted(mpd),v=v,cands=cands,PProw=list(PP[r-100]) if r-100<len(PP) else None,XProw=list(XP[r-100]) if r-100<len(XP) else None,nbridge=len(BRIDGES)))\n"+c)
if V=='DBG2':
    b="                if all(np.allclose(dp_[po], ds_[so], rtol=1e-2, atol=1e-3) for po, so in p_to_s_out.items()) and any(np.abs(dp_[po]).max() > 1e-5 for po in p_to_s_out):\n                    good.append(m)"
    assert src.count(b)==1
    src=src.replace(b,"                DBG_.append(dict(rc=(r,c),cand=m,dp={str(po):float(np.abs(dp_[po]).max()) for po in p_to_s_out},ds={str(so):float(np.abs(ds_[so]).max()) for po,so in p_to_s_out.items()},eq={str(po):bool(np.allclose(dp_[po], ds_[so], rtol=1e-2, atol=1e-3)) for po,so in p_to_s_out.items()}))\n"+b)
if V=='V4':
    # V4: risoluzione MaterialParams per RISPOSTA (coseno fra variazioni delle uscite), non per valore/ampiezza assoluta
    a="        if len(cands) > 1:\n            # ancora ambiguo: perturba"
    assert src.count(a)==1
    src=src.replace(a,"        base_cands = list(cands)\n        if len(cands) == 0: cands = list(sorted(ms))\n        if len(cands) > 1:\n            # ancora ambiguo: perturba")
    old="""            good = []
            for m in cands:
                ds_ = blk_delta(sprog, s0, s1, st_s, envx, m, list(p_to_s_out.values()))
                if all(np.allclose(dp_[po], ds_[so], rtol=1e-2, atol=1e-3) for po, so in p_to_s_out.items()) and any(np.abs(dp_[po]).max() > 1e-5 for po in p_to_s_out):
                    good.append(m)
"""
    assert src.count(old)==1
    new="""            good = []; scores = {}
            vp_ = np.concatenate([np.ravel(dp_[po]) for po, so in p_to_s_out.items()]) if p_to_s_out else np.zeros(1)
            npv = float(np.linalg.norm(vp_))
            for m in cands:
                ds_ = blk_delta(sprog, s0, s1, st_s, envx, m, list(p_to_s_out.values()))
                vs_ = np.concatenate([np.ravel(ds_[so]) for po, so in p_to_s_out.items()]) if p_to_s_out else np.zeros(1)
                nsv = float(np.linalg.norm(vs_))
                scores[m] = (float(vp_ @ vs_ / (npv * nsv)) if npv > 1e-6 and nsv > 1e-6 else (1.0 if npv <= 1e-6 and nsv <= 1e-6 else 0.0), nsv / npv if npv > 1e-6 else 0.0)
            if npv > 1e-6:
                rk = sorted(scores.items(), key=lambda kv: -kv[1][0])
                if rk[0][1][0] >= 0.98 and (len(rk) == 1 or rk[0][1][0] - rk[1][1][0] >= 0.02): good = [rk[0][0]]
            DBG_.append(dict(rc=(r, c), npv=npv, scores={str(k): [round(v[0], 4), round(v[1], 3)] for k, v in sorted(scores.items(), key=lambda kv: -kv[1][0])[:4]}, base=base_cands, pick=good))
"""
    src=src.replace(old,new)
if V=='V5':
    # V5: ponti estesi (coppie con blocchi luci Xbox e PC equivalenti, bridge_ext.py) + filtro per valore insensibile a lane NaN
    b="""            for XP2, PP2 in BRIDGES[1:]:
                v2 = PP2[r - 100][c] if r - 100 < len(PP2) else None
                if v2 is None: continue
                cands = [m for m in cands if m[0] - 100 < len(XP2) and abs(XP2[m[0] - 100][m[1]] - v2) < 1e-6]
"""
    assert src.count(b)==1
    src=src.replace(b,"""            for XP2, PP2 in BRIDGES[1:]:
                v2 = PP2[r - 100][c] if r - 100 < len(PP2) else None
                if v2 is None or v2 != v2: continue
                cands = [m for m in cands if m[0] - 100 < len(XP2) and (XP2[m[0] - 100][m[1]] != XP2[m[0] - 100][m[1]] or abs(XP2[m[0] - 100][m[1]] - v2) < 1e-6)]
""")
if V=='V3':
    a="        if len(cands) > 1:\n            # ancora ambiguo: perturba"
    assert src.count(a)==1
    src=src.replace(a,"        base_cands = list(cands)\n        if len(cands) != 1: cands = list(sorted(ms))\n        if len(cands) > 1:\n            # ancora ambiguo: perturba")
    b="any(np.abs(dp_[po]).max() > 1e-5 for po in p_to_s_out):\n                    good.append(m)"
    assert src.count(b)==1
    c2="            elif not good and all(np.abs(dp_[po]).max() <= 1e-5 for po in p_to_s_out): cands = cands[:1]"
    assert src.count(c2)==1
    d3="            if len(good) == 1: cands = good\n"
    assert src.count(d3)==1
    src=src.replace(d3,"            DBG_.append(dict(rc=(r,c),n_cands=len(cands),good=good,effect=float(max((float(np.abs(dp_[po]).max()) for po in p_to_s_out),default=0)),n_out=len(p_to_s_out),base=base_cands))\n"+d3)
    src=src.replace(c2,"            elif not good and all(np.abs(dp_[po]).max() <= 1e-5 for po in p_to_s_out): cands = base_cands[:1]\n            else: cands = [] if not base_cands else base_cands")
if V=='V1':
    a="        if (r, c) in cands: cands = [(r, c)]\n"
    assert src.count(a)==1
    src=src.replace(a,"        if (r, c) in ms: cands = [(r, c)]; MPLOG_.append(('ident-layout', r, c, bool((r, c) in cands_value)))\n        elif (r, c) in cands: cands = [(r, c)]\n")
    b="        cands = [m for m in sorted(ms) if v is not None and m[0] - 100 < len(XP) and abs(XP[m[0] - 100][m[1]] - v) < 1e-6]\n"
    assert src.count(b)==1
    src=src.replace(b,b+"        cands_value = list(cands)\n")
src=src.replace("class Fail(Exception):","MPLOG_ = []\nDBG_ = []\nclass Fail(Exception):",1)
mod=types.ModuleType('f9_transplant'); mod.__file__=S4+'/f9_transplant.py'
sys.modules['f9_transplant']=mod
exec(compile(src,S4+'/f9_transplant.py','exec'),mod.__dict__)
import f12_build_all as F12     # importa f10_build_dlc (che fa 'from f9_transplant import *' -> modulo patchato gia' in sys.modules)
assert F12.build is mod.build and F12.Fail is mod.Fail
from f12_build_all import *
res={}; log=[]; cnt=collections.Counter()
L=libs(); D,DM,X,P=L['D'],L['DM'],L['X'],L['P']
lit={int(r['id_xbox']):r for r in __import__('csv').DictReader(open(S4+'/illuminati.tsv'),delimiter='\t')}
rev=collections.defaultdict(list)
for x,p in x2p().items(): rev[p].append(x)
occ,secs=material_occurrences(SRC,DM,lambda dl: dl in lit)
donor_cache={}
t0=time.time()
ONLY=[int(x) for x in os.environ.get('ONLY','').split(',') if x]
for mid,items in sorted(occ.items()):
    if ONLY and mid not in ONLY: continue
    dl=struct.unpack_from('>4I',DM[mid][0],0x28)[2]
    why=shared_problem(dl,items,secs)
    if why: res[mid]=dict(status='escluso-lifetime/regime-B',why=why); continue
    s=canonical_material(items); pc=struct.unpack_from('<4I',s.data,0x28)[2]
    if dl not in donor_cache:
        need={k for k,x in enumerate(P[pc]['slots']) if x!=0xffffffff} if pc in P else set(range(8))
        pref=[(x,pc) for x in rev[pc]]; ok=None
        for cand in find_donors('D',dl,0,want=12,prefer=pref):
            have={k for k,x in enumerate(P[cand[1]]['slots']) if x!=0xffffffff}
            if not need<=have: continue
            r1=find_donors('D',dl,1,want=1,prefer=[cand])
            if r1 and r1[0]==cand: ok=cand; break
        donor_cache[dl]=ok
    dn=donor_cache[dl]
    if dn is None: res[mid]=dict(status='escluso-nessun-donatore',why='nessun donatore'); continue
    xs,pd=dn; bridge=material_pairs(xs,pd)
    if V=='V5':
        import bridge_ext; bridge=list(bridge)+[(None,None,a_,b_) for a_,b_,_ in bridge_ext.extra_bridges(xs,pd)]
    XPm=params(f9_common._Sec(*DM[mid]),'be'); PPm=params(s,'le'); bad=None; n_ident=0
    for k,e in enumerate(P[pd]['slots']):
        if e==0xffffffff: continue
        xblob=D[dl]['entries'][D[dl]['slots'][k&1]]['blob']
        try:
            mo=material_opts(mid); mod.MPLOG_.clear()
            T,info=build(xblob,P[pd]['entries'][e]['blob'],X[xs]['entries'][X[xs]['slots'][k&1]]['blob'],[(m_[2],m_[3]) for m_ in bridge],log=[],x_opts=mo)
            n_ident+=len(mod.MPLOG_)
            T,binfo=bind_material(T,XPm,PPm)
            bc,n,off,probs=offline_ok(T,xblob,XPm,opts=mo)
        except (mod.Fail,xenos2sm3.Reject) as ex: bad='slot %d: %s'%(k,str(ex)[:140]); break
        except Exception as ex: bad='slot %d: ECCEZIONE %s'%(k,repr(ex)[:140]); break
        if probs: bad='slot %d: %s'%(k,probs); break
    res[mid]=dict(status='costruito' if not bad else 'escluso-offline',why=bad,donor=list(dn),n_ident=n_ident)
    if V in ('DBG','V3','V4') and mod.DBG_: print('   DBG',mid,json.dumps(mod.DBG_[-1],default=str)[:900],flush=True); mod.DBG_.clear()
    if V=='DBG2':
        for d_ in mod.DBG_: print('   DBG2',mid,json.dumps(d_,default=str)[:600],flush=True)
        mod.DBG_.clear()
    print(V,mid,res[mid]['status'],bad or '',flush=True)
cnt=collections.Counter(r['status'] for r in res.values())
json.dump(res,open(f'{OUTA}/{V}.json','w'),indent=1)
open(f'{OUTA}/{V}.md','w').write(f'# {V}\n'+', '.join(f'{k} {v}' for k,v in cnt.items())+f'\n\ntempo {time.time()-t0:.0f}s\n\n'+'\n'.join(f"- mat {m}: {r['status']} {r['why'] or ''}" for m,r in sorted(res.items()) if r['status']!='costruito')+'\n')
print(V,dict(cnt),'%.0fs'%(time.time()-t0))
