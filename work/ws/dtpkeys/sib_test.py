import sys,collections; sys.path.insert(0,'tools')
import dtp_keys as K, dtp_audit as A
def sibkeys(xd,rel):
    ptr,idl,it,tc,sh=K.prep(xd,rel); n=len(xd)//4; slots=set(ptr)|idl
    out=[]
    for i in range(n):
        if 4*i in slots: continue
        k=(sh[i],)+tuple(('|' if j>=n else tc[j] if tc[j]!='.' else sh[j]) for j in (i+1,i+2))
        out.append((4*i,k))
    return out
def sib_flags(xd,rel,pd,minsib=3):
    g=collections.defaultdict(list)
    for o,k in sibkeys(xd,rel):
        c=A.cls(xd[o:o+4],pd[o:o+4])
        if c==K.ALL: continue            # palindromic/no evidence
        g[k].append((o,c))
    res=[]
    for k,l in g.items():
        if len(l)<minsib+1: continue
        cnt=[sum(1 for _,c in l if c>>b&1) for b in range(5)]
        for o,c in l:
            if c==0: continue
            a=0
            for b in range(5):
                if cnt[b]-(c>>b&1)==len(l)-1: a|=1<<b
            if a and a!=K.ALL and not c&a: res.append((o,k,c,a,len(l)-1))
    return res
if __name__=='__main__':
    nb=0; tot=0; ex=collections.Counter()
    for x,p,xb,pc,xr in A.base_pairs():
        r=sib_flags(xb['data'],xr,pc['data'])
        nb+=len(r); ex[x]+=len(r) if r else 0
    print('base FP (sibling outliers on REAL PC bytes):',nb,'in',sum(1 for v in ex.values() if v),'DTPs of',len(ex))

def run():
    import dtp_audit as A2
    for ms in (3,5,8,12):
        nb=0
        for x,p,xb,pc,xr in A.base_pairs(): nb+=len(sib_flags(xb['data'],xr,pc['data'],ms))
        print('minsib',ms,'base FP',nb)
