import sys, pickle, collections, math, struct
sys.path.insert(0,'work/ws/fpfloat'); sys.path.insert(0,'tools')
from feat import *
import drm_write as DW
S0,S1,CONF=pickle.load(open('work/ws/fpfloat/stat1.pkl','rb'))
tot=[]
for a,b in zip(S0,S1):
    t=collections.defaultdict(lambda:[0]*6)
    for s in (a,b):
        for k,v in s.items():
            for i in range(6): t[k][i]+=v[i]
    tot.append(dict(t))
MIN_N=20
rules=[]
for d in tot:
    r={}
    for k,v in d.items():
        if v[0]>=MIN_N:
            i=max(range(5),key=lambda j:v[j+1])
            if v[i+1]==v[0]: r[k]=i
    rules.append(r)
def plaus(v): return math.isfinite(v) and 1e-4<=abs(v)<=1e6
INST=A.INSTALLED+['mods_fix20','chain_aim/mods_chainfix_min']
order=[5,3,1,4,2,0]
res=[]
files=A.overlay(INST)
files={k:v for k,v in files.items() if k!='g_pda.drm'}
for rel,path in sorted(files.items()):
    xs=A.xsecs(rel)
    if xs is None: continue
    D=DW.read(open(path,'rb').read(),'le')
    for x,i in A.section_pairs(xs,D):
        sec=D.sections[i]
        if x['type']!=7 or len(sec.data)!=len(x['data']): continue
        if A.base_content(x): continue
        xd=x['data']; pd=sec.data; xr=R.parse(x['reloc'],'be')
        for o,k,ks,sh in words(xd,xr):
            xw=xd[o:o+4]; pw=pd[o:o+4]
            c=A.cls(xw,pw)
            if c==A.ALL or c==0: continue
            for ci in order:
                d,us=CONF[ci]
                r=rules[ci].get((k,ks[d-1],sh if us else 0))
                if r is not None: break
            else: continue
            if c>>r&1: continue
            fx=struct.unpack('>f',xw)[0]; fp=struct.unpack('<f',pw)[0]
            res.append(dict(file=rel,id=sec.id,off=o,xbox=xw.hex(),pc=pw.hex(),rule=A.NAMES[r],ci=ci,got=[A.NAMES[j] for j in range(5) if c>>j&1],
                            fgate=bool(A.NAMES[r]=='s32' and plaus(fx) and not plaus(fp)),k=k,key=repr(ks[0])))
pickle.dump(res,open('work/ws/fpfloat/scan1.pkl','wb'))
print(len(res), collections.Counter((r['rule'],r['fgate']) for r in res))
byd=collections.Counter((r['file'],r['id']) for r in res if r['fgate'])
for k,v in byd.most_common(60): print(v,k)
