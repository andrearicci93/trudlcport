"""roles.py - firma di RUOLO per ogni componente MaterialParams da un'IR Xenos (xenos_xlat.IRBuilder):
   ('uv', sampler)         il componente entra nelle coordinate di una fetch del sampler (scala UV)
   ('mul', {samplers})     moltiplica (n-ario) un sottoalbero che contiene fetch di quei sampler (tinta/peso del layer)
   ('add', {samplers})     idem additivo
   ('f', ctx)              altrimenti: contesto = tipo del genitore (e dei fratelli: costanti nominate/litterali)
Le firme di D (shader DLC) e S (surrogato) si confrontano: componenti con firma uguale e univoca da entrambi i lati = mappa."""
import sys,os,collections
sys.path.insert(0,'/path/to/trudlcport/work/ws/xenos'); sys.path.insert(0,'/path/to/trudlcport/tools')
import xenos_xlat as X, xenos_map as M
sys.setrecursionlimit(100000)
LEAF={'k','P','C','V','U','B'}
def children(nd):
    k=nd[0]
    if k in LEAF: return []
    if k=='T': return list(nd[4:])
    if k=='TC': return [nd[1]]
    return [c for c in nd[1:] if isinstance(c,int) and not isinstance(c,bool)]
def reach(ir,roots):
    seen=set(); st=list(roots)
    while st:
        n=st.pop()
        if n in seen: continue
        seen.add(n); st.extend(children(ir.nodes[n]))
    return seen
def analyse(blob):
    sh,b,roots=M.build_ir(blob); ir=b.ir
    rs=[r for r in (roots.values() if isinstance(roots,dict) else roots)]
    flat=[]
    for r in rs:
        flat.extend(r if isinstance(r,(list,tuple)) else [r])
    nodes=reach(ir,flat)
    sname=lambda cidx:(sh.samplers.get(cidx) or {}).get('name','s%d'%cidx)
    memo={}; lpm={}
    def samps(n):                      # sampler names raggiungibili da n (via T)
        if n in memo: return memo[n]
        nd=ir.nodes[n]; res=set()
        if nd[0]=='TC' and ir.nodes[nd[1]][0]=='T': res.add((sname(ir.nodes[nd[1]][1]),nd[2]))
        elif nd[0]=='T': res.add((sname(nd[1]),None))
        if nd[0]!='TC' or ir.nodes[nd[1]][0]!='T':
            for c in children(nd): res|=samps(c)
        else:
            for c in ir.nodes[nd[1]][4:]: res|=samps(c)
        r=frozenset(res); memo[n]=r; return r
    roles=collections.defaultdict(collections.Counter)
    for n in nodes:
        nd=ir.nodes[n]
        if nd[0]=='T':
            for ax,c in enumerate(nd[4:]):
                for p in leaves_P(ir,c,lpm): roles[p][('uv',sname(nd[1]),ax)]+=1
        elif nd[0] in ('mul','add'):
            ch=nd[1:]
            for c in ch:
                if ir.nodes[c][0]=='P':
                    others=frozenset().union(*[samps(o) for o in ch if o!=c]) if len(ch)>1 else frozenset()
                    if others: roles[(ir.nodes[c][1],ir.nodes[c][2])][(nd[0],others)]+=1
                    else: roles[(ir.nodes[c][1],ir.nodes[c][2])][(nd[0]+'0',tuple(sorted(str(ir.nodes[o][:1]) for o in ch if o!=c)))]+=1
        else:
            for c in children(nd):
                if ir.nodes[c][0]=='P': roles[(ir.nodes[c][1],ir.nodes[c][2])][('f',nd[0])]+=1
    snames={}
    for n in nodes:
        nd=ir.nodes[n]
        if nd[0]=='T': snames[sname(nd[1])]=nd[2]
    return sh,ir,Roles(roles,snames)
class Roles(dict):
    def __init__(self,d,snames): super().__init__(d); self.snames=snames
    def renamed(self,alias):
        def rn(r):
            if r[0]=='uv': return ('uv',alias.get(r[1],r[1]),r[2])
            if r[0] in ('mul','add'): return (r[0],frozenset((alias.get(a,a),ch) for a,ch in r[1]))
            return r
        out=collections.defaultdict(collections.Counter)
        for k,c in self.items():
            for r,v in c.items(): out[k][rn(r)]+=v
        return Roles(out,self.snames)
_lp={}
def leaves_P(ir,n,memo):
    key=n
    if key in memo: return memo[key]
    nd=ir.nodes[n]
    if nd[0]=='P': r=frozenset([(nd[1],nd[2])])
    elif nd[0]=='T': r=frozenset()      # non scendere in un'altra fetch
    else:
        r=frozenset()
        for c in children(nd): r|=leaves_P(ir,c,memo)
    memo[key]=r; return r
if __name__=='__main__':
    L=X.load_libs(); D,Xl=L['D'],L['X']
    dl,sl=int(sys.argv[1]),int(sys.argv[2])
    ld=D.get(dl) or Xl[dl]; ls=Xl[sl]
    for si,(sa,sb) in enumerate(zip(ld['slots'],ls['slots'])):
        if sa==0xffffffff or sb==0xffffffff: continue
        shd,ird,rd=analyse(ld['entries'][sa]['blob']); shs,irs,rs=analyse(ls['entries'][sb]['blob'])
        print('slot',si,'D params',len(rd),'S params',len(rs))
        break
    print('--- D'); 
    for k in sorted(rd): print(k,dict(rd[k]))
    print('--- S')
    for k in sorted(rs): print(k,dict(rs[k]))
