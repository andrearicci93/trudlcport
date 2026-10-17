"""feature extraction shared by exploration scripts"""
import sys, struct, bisect, collections
sys.path.insert(0,'tools')
import dtp_audit as A, drm_reloc as R
from generic_type0 import shape

def words(xd, rel, depth=3):
    """yield (o, k, (k1,k2,k3 path keys), shape) for every non-slot, non-string 4-aligned word of an Xbox DTP"""
    slots=set(rel.pointer_offsets()); idsl=set(rel.id_offsets()); it=dict(rel.internal)
    both=slots|idsl
    tg=sorted({0}|{t for t in it.values() if t<len(xd)})
    refs={}
    for o,t in sorted(it.items()): refs.setdefault(t,o)
    strw=set()
    for a,z,kd in A.string_spans(xd,rel):
        for q in range(a-a%4,z+1,4): strw.add(q)
    memo={}
    def start(o): return tg[bisect.bisect_right(tg,o)-1]
    def rkey(s,d):
        m=memo.get((s,d))
        if m is not None: return m
        o=refs.get(s)
        if o is None: r=('root',len(xd) if s==0 else -1)
        else:
            ps=start(o)
            w=struct.unpack_from('>I',xd,o-4)[0] if o>=4 and (o-4) not in both else 99
            tag=w if w<=13 else -1
            r=(tag,o-ps, rkey(ps,d-1) if d>1 else None)
        memo[s,d]=r; return r
    cur=-1; ks=None
    for o in range(0,len(xd)-3,4):
        if o in both or o in strw: continue
        s=start(o)
        if s!=cur: cur=s; ks=tuple(rkey(s,d) for d in range(1,depth+1))
        yield o, min(o-s,0x400), ks, shape(xd[o:o+4])
