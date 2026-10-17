import sys; sys.path.insert(0,'tools')
import dtp_keys as K, dtp_audit as A, pickle, collections
d=pickle.load(open(K.RULES,'rb')); folds=d['folds']
want=set(int(a) for a in sys.argv[1:])
shown=collections.Counter()
for x,p,xb,pc,xr in A.base_pairs():
    if x not in want: continue
    fo=K.fold(xb['src']); xd,pd=xb['data'],pc['data']; rl=folds[1-fo]
    # fraction of non-perm words
    nn=0;tot=0
    for o,ks in K.keys_of(xd,xr):
        c=A.cls(xd[o:o+4],pd[o:o+4]); 
        if c==K.ALL: continue
        tot+=1; nn+= c==0
        if c==0: continue
        f,m=K.decide(ks,rl)
        if m and not c&m and shown[x]<6:
            shown[x]+=1; print(x,xb['src'],len(xd),'%#x'%o,xd[o:o+4].hex(),pd[o:o+4].hex(),f,[K.NAMES[i] for i in range(5) if m>>i&1],ks[f])
    print(x,'class0 words',nn,'of',tot)
