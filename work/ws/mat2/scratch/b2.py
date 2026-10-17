import sys,struct,collections
sys.path.insert(0,'tools')
import material_reslot as MR
from shaderlib import constants
from d3d9_consts import used_consts
L=MR.libs(); P=L['P']; PM=L['PM']
LO,HI=100,132
def libinfo(lib):
    """per permutation: (declared MaterialParams count, used count)"""
    res=[]
    for s in sorted(set(lib['slots'])-{0xFFFFFFFF}):
        b=lib['entries'][s]['blob']
        v,c=constants(b,'p')
        decl=max([rc for n,rs,ri,rc in c if n=='MaterialParams' and rs==2] or [0])
        u,rel=used_consts(b)
        uu=[r for r in u if LO<=r<HI]
        res.append((decl, (max(uu)-LO+1) if uu else 0, len(rel)))
    return res
if __name__=='__main__':
    st=collections.Counter(); ex=[]
    for pid,(d,r) in sorted(PM.items()):
        pt=struct.unpack_from('<4I',d,0x28); n=struct.unpack_from('<I',d,0x58)[0]
        infos=[]
        for s in pt[:3]:
            if s and s in P and P[s]['kind']==1: infos+=libinfo(P[s])
        if not infos: st['no ps']+=1; continue
        dmax=max(i[0] for i in infos); umax=max(i[1] for i in infos)
        dmin=min(i[0] for i in infos); umin=min(i[1] for i in infos)
        st['mat']+=1
        st['n>=umax']+= n>=umax; st['n==umax']+= n==umax; st['n==dmax']+=n==dmax; st['n>=dmax']+= n>=dmax
        st['n>=umin']+= n>=umin
        st['umax<=dmax']+= umax<=dmax
        st['rel used']+= any(i[2] for i in infos)
        if n<umax: ex.append((pid,n,umax,dmax,umin))
    for k,v in st.items(): print(k,v)
    print(ex[:30], len(ex))
