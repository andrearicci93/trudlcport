import sys, pickle, collections, math, struct
sys.path.insert(0,'work/ws/fpfloat'); sys.path.insert(0,'tools')
from feat import *
S0,S1,CONF=pickle.load(open('work/ws/fpfloat/stat1.pkl','rb'))
MIN_N=20
def mk(st):
    out=[]
    for d in st:
        r={}
        for k,v in d.items():
            if v[0]>=MIN_N:
                i=max(range(5),key=lambda j:v[j+1])
                if v[i+1]==v[0]: r[k]=i
        out.append(r)
    return out
R=[mk(S1),mk(S0)]       # R[f] = rules to use on fold f (learned from other fold)
def plaus(v): return math.isfinite(v) and 1e-4<=abs(v)<=1e6
orders={'d1s':[1],'d2s':[3],'d1':[0],'d2':[2],'DL':[5,3,1,4,2,0]}
cnt=collections.defaultdict(collections.Counter)
infos=0
for x,p,xb,pc,xr in A.base_pairs():
    f=A.fold(xb['src']); xd=xb['data']; pd=pc['data']
    for o,k,ks,sh in words(xd,xr):
        xw=xd[o:o+4]; pw=pd[o:o+4]
        c=A.cls(xw,pw)
        if c==A.ALL or c==0: continue
        infos+=1
        for name,order in orders.items():
            for ci in order:
                d,us=CONF[ci]
                r=R[f][ci].get((k,ks[d-1],sh if us else 0))
                if r is not None: break
            else: continue
            C=cnt[name]; C['cov']+=1
            if not c>>r&1:
                C['flag']+=1
                want=bytes(xw[j] for j in A.PERMS[A.NAMES[r]])
                if A.NAMES[r]=='s32' and plaus(struct.unpack('>f',xw)[0]) and not plaus(struct.unpack('<f',pw)[0]):
                    C['flag_floatgate']+=1
                    if C['flag_floatgate']<=3: print(name,x,hex(o),xw.hex(),pw.hex())
print('informative',infos)
for n,C in cnt.items(): print(n,dict(C),'cov %.3f'%(C['cov']/infos))
