import sys, collections, struct, bisect, zlib
sys.path.insert(0,'tools')
import dtp_audit as A, drm_reloc as R
PERMS=A.PERMS; NAMES=A.NAMES
def ctx_words(xd, rel, depth):
    slots=set(rel.pointer_offsets()); idsl=set(rel.id_offsets()); it=dict(rel.internal)
    tg=sorted({0}|{t for t in it.values() if t<len(xd)}); tgs=set(tg)
    refs={}
    for o,t in sorted(it.items()): refs.setdefault(t,o)
    def start(o): return tg[bisect.bisect_right(tg,o)-1]
    memo={}
    def rkey(s,d):
        if (s,d) in memo: return memo[s,d]
        o=refs.get(s)
        if o is None: r=('root',len(xd) if s==0 else -1)
        else:
            ps=start(o)
            tag=('N',struct.unpack_from('>I',xd,o-4)[0]) if o>=4 and (o-4) not in slots and (o-4) not in idsl and struct.unpack_from('>I',xd,o-4)[0]<=13 else ('S',)
            r=(tag,o-ps, rkey(ps,d-1) if d>1 else None)
        memo[s,d]=r; return r
    out=[]
    for o in range(0,len(xd)-3,4):
        if o in slots or o in idsl: continue
        s=start(o)
        out.append((o,o-s,[rkey(s,d) for d in range(1,depth+1)]))
    return out
def cls(xw,pw): return A.cls(xw,pw)
if __name__=='__main__':
    D=3
    pairs=list(A.base_pairs())
    # stats per depth: key=(k,rkey_d,shape?)
    for d in range(1,D+1):
      for useshape in (0,1):
        st=[collections.defaultdict(lambda:[0]*6) for _ in range(2)]
        for x,p,xb,pc,xr in pairs:
            f=A.fold(xb['src']); xd=xb['data']; pd=pc['data']
            for o,k,rk in ctx_words(xd,xr,d):
                c=cls(xd[o:o+4],pd[o:o+4])
                if c==A.ALL or c==0: continue
                key=(min(k,0x400),rk[d-1],A.shape(xd[o:o+4]) if useshape else 0)
                v=st[f][key]; v[0]+=1
                for i in range(5):
                    if c>>i&1: v[i+1]+=1
        tot=collections.defaultdict(lambda:[0]*6)
        for s in st:
            for k,v in s.items():
                for i in range(6): tot[k][i]+=v[i]
        rules=A.make_rules(tot)
        nw=sum(v[0] for v in tot.values()); cov=sum(tot[k][0] for k in rules)
        print('depth',d,'shape',useshape,'keys',len(tot),'ruled',len(rules),'covered words %d/%d = %.3f'%(cov,nw,cov/nw))
