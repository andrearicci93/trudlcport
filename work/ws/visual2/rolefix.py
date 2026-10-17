"""rolefix.py - pianificazione della mappa MaterialParams D->S per FIRMA DI RUOLO (vedi roles.py / rolemap.py) sui materiali DLC convertiti.
Comandi: selftest | scan | plan MID"""
import sys,os,collections,struct,json,pickle
sys.path.insert(0,'/path/to/trudlcport/work/ws/visual2'); sys.path.insert(0,'/path/to/trudlcport/tools')
import roles as RO, rolemap as RM, xenos_xlat as X, param_auto as PA, material_convert as MC, drm_reloc as R
L=X.load_libs(); D,Xl=L['D'],L['X']
W='/path/to/trudlcport/work/render'
smap={int(k):v for k,v in json.load(open(W+'/dlc_shader_map.json')).items()}
def lib_pair_map(dl,sl):
    """-> dict S comp -> Counter(D comp) over the permutation slots; plus set of S comps referenced"""
    votes,sref,dref,ns=RM.pair_maps(dl,sl)
    return votes,sref,dref,ns
_cache={}
def pair(dl,sl):
    if (dl,sl) not in _cache: _cache[dl,sl]=lib_pair_map(dl,sl)
    return _cache[dl,sl]
def selftest(n=60):
    import random; random.seed(2)
    ks=[k for k,v in Xl.items() if v['kind']==1]; random.shuffle(ks)
    ok=bad=0; nonid=[]
    for k in ks[:n]:
        v,sref,dref,ns=pair(k,k)
        # identity: every voted S comp maps to itself with no conflict
        good=all(len(c)==1 and next(iter(c))==s for s,c in v.items())
        ok+=good; bad+=not good
        if not good: nonid.append((k,[(s,dict(c)) for s,c in v.items() if not(len(c)==1 and next(iter(c))==s)][:3]))
    print('selftest base libs vs themselves: identita',ok,'non identita',bad); 
    for x in nonid[:8]: print('  ',x)
if __name__=='__main__':
    if sys.argv[1]=='selftest': selftest(int(sys.argv[2]) if len(sys.argv)>2 else 60)

# ------------------------------------------------------------------ pianificazione per materiale
MATS,MSH,MX2P=None,None,None
import material_reslot as MR
rules=pickle.load(open(W+'/param_rules.pkl','rb'))
def init():
    global MATS,MSH,MX2P
    MATS,MSH,MX2P=MR.dlc_tables()
def plan(xmid,verbose=False):
    """-> dict(passes=[(pos,dl,cls,sl,nmap,nref)], map={S comp:(D comp)}, conflicts, unmapped=set(S comps referenced but unmapped), nS)"""
    xd,xr=L_DM[xmid]
    ids=struct.unpack_from('>4I',xd,0x28)
    out=dict(passes=[],map={},conflict=set(),unmapped=set(),nS=0)
    comb=collections.defaultdict(collections.Counter); refs=set()
    for pos in (0,1,2):
        s=ids[pos]
        if not s: continue
        m=smap[s]
        if m['cls'] not in ('C1','C2'): out['passes'].append((pos,s,m['cls'],m['surrogate'],None,None)); continue
        v,sref,dref,ns=pair(s,m['surrogate'])
        for k,c in v.items():
            for d,n in c.items(): comb[k][d]+=n
        refs|=sref
        out['passes'].append((pos,s,m['cls'],m['surrogate'],len(v),len(sref)))
    for k,c in comb.items():
        if len(c)==1: out['map'][k]=next(iter(c))
        else: out['conflict'].add(k)
    out['unmapped']=refs-set(out['map'])-out['conflict']; out['refs']=refs
    return out
import pickle as _p
L_DM=_p.load(open('/path/to/trudlcport/work/render/shaderlibs.pkl','rb'))['DM']
if __name__=='__main__' and sys.argv[1]=='plan':
    init()
    for m in map(int,sys.argv[2:]):
        p=plan(m); print(m,p['passes']); 
        xd,xr=L_DM[m]; vx=MC.read_params(xd,xr,'>')
        print(' refs',len(p['refs']),'mapped',len(p['map']),'conflict',sorted(p['conflict']),'unmapped',sorted(p['unmapped']))
        ch=[(k,d,round(vx[d[0]][d[1]],3),round(vx[k[0]][k[1]],3)) for k,d in sorted(p['map'].items()) if d!=k and d[0]<len(vx) and k[0]<len(vx)]
        print(' non-identita (S<-D, valoreD, valoreIdentita):',ch)

# ------------------------------------------------------------------ calcolo dei parametri PC nuovi
XM_=None
def new_params(xmid,p=None):
    """-> (current pc vec list, new pc vec list, info) o None"""
    global XM_
    init() if MATS is None else None
    m=MATS[xmid]
    if m['source']!='converted': return None
    p=p or plan(xmid)
    if not p['map']: return None
    xd,xr=L_DM[xmid]; vx=MC.read_params(xd,xr,'>')
    pd,pr=m['data'],m['reloc']
    ip=dict(R.parse(pr,'le').internal); n=struct.unpack_from('<I',pd,0x58)[0]
    cur=[struct.unpack_from('<4f',pd,ip[0x5C]+16*i) for i in range(n)]
    flatD=[v for q in vx for v in q]
    # S layout (Xbox form) = D flat con le componenti mappate sovrascritte
    flatS=list(flatD)
    need=max([4*k[0]+k[1] for k in p['map']]+[4*n-1])+1
    flatS+= [0.0]*(need-len(flatS))
    for (si,sc),(di,dc) in p['map'].items():
        flatS[4*si+sc]=flatD[4*di+dc] if 4*di+dc<len(flatD) else 0.0
    bm=MSH.get(xmid,{}).get('base_material')
    rule=None
    if bm is not None:
        bd=L_XM[bm][0]; rule=rules.get(MC.shift_key(bd) if hasattr(MC,'shift_key') else MC.shader_key(bd))
    # ricostruzione di cio' che fa material_dlc oggi (per verificare 'cur' = copia D)
    def build(flat,vv):
        if rule is not None and len(vv)==struct.unpack_from('>I',L_XM[bm][0],0x58)[0]:
            return [tuple(q) for q in MC.apply_rule(rule,[tuple(flat[4*k:4*k+4]) for k in range(len(flat)//4)])]
        v=[tuple(flat[4*k:4*k+4]) for k in range(len(flat)//4)]
        return (v+[(0.0,)*4]*n)[:n]
    base=build(flatD,vx); new=build(flatS,vx)
    return cur,base,new,rule
L_XM=_p.load(open('/path/to/trudlcport/work/render/shaderlibs.pkl','rb'))['XM']
def scan():
    init(); rows=[]; c=collections.Counter()
    for xmid,m in sorted(MATS.items()):
        if m['source']!='converted' or xmid==21118: continue
        try: r=new_params(xmid)
        except Exception as e: c['err']+=1; continue
        if r is None: c['no map']+=1; continue
        cur,base,new,rule=r
        if [tuple(round(x,5) for x in v) for v in cur]!=[tuple(round(x,5) for x in v) for v in base]: c['cur!=D copy (other rule applied)']+=1; continue
        ch=[(i,j,round(a[j],3),round(b[j],3)) for i,(a,b) in enumerate(zip(base,new)) for j in range(4) if abs(a[j]-b[j])>1e-6]
        if ch: c['changed']+=1; rows.append((xmid,len(ch),max(abs(a[2]-a[3])/(abs(a[2])+1e-3) for a in ch)))
        else: c['mapped but no value change']+=1
    print(dict(c)); return rows
if __name__=='__main__' and sys.argv[1]=='scan':
    rows=scan(); print(len(rows)); print(sorted(rows,key=lambda r:-r[2])[:20])
