import sys,os,struct,json,collections
sys.path.insert(0,'/path/to/trudlcport/tools')
import material_reslot as MR
from shaderlib import constants
from drm import cdrm_decode, sections_with_data
import drm_reloc as R
T='/path/to/trudlcport/'
C=json.load(open('out/census.json'))
L=MR.libs(); X,P,DM=L['X'],L['P'],L['DM']
MODS=T+'work/baseline/B8/mods/'
def names(lib,plat):
    s=set()
    if lib is None or lib['kind']!=1: return s
    for sl in set(lib['slots'])-{0xFFFFFFFF}:
        v,c=constants(lib['entries'][sl]['blob'],plat)
        for n,rs,ri,rc in c: s.add((n,rs))
    return s
out={}
seen=set()
for k,v in C.items():
    if not v['drm']: continue
    mid=int(k); drm=sorted(v['drm'])[0]
    p=MODS+drm.replace('\\','/')
    if not os.path.exists(p):
        for dp,dn,fn in os.walk(MODS):
            for f in fn:
                if os.path.relpath(os.path.join(dp,f),MODS).lower().replace('/','\\')==drm: p=os.path.join(dp,f)
    raw=cdrm_decode(open(p,'rb').read(),'le'); _,secs=sections_with_data(raw,'le')
    sec=[s for s in secs if s['type']==10 and s['id']==mid][0]
    pd,pr=sec['data'],sec['reloc']
    pt=struct.unpack_from('<4I',pd,0x28)
    pn=set();
    for x in pt[:3]:
        if x: pn|=names(P.get(x),'p')
    r={'pt':pt[:3],'nparam':struct.unpack_from('<H',pd,0x4e)[0] if False else None}
    r['pc_samp']=sorted(n for n,rs in pn if rs==3)
    r['pc_const']=sorted(n for n,rs in pn if rs!=3)
    if mid in DM:
        xd,xr=DM[mid]; xt=struct.unpack_from('>4I',xd,0x28)
        xn=set()
        for x in xt[:3]:
            if x: xn|=names(X.get(x),'x')
        r['xt']=xt[:3]; r['x_samp']=sorted(n for n,rs in xn if rs==3); r['x_const']=sorted(n for n,rs in xn if rs!=3)
    else: r['xt']=None
    te=MR.tex_entries(pd,R.parse(pr,'le'),'<')
    r['tex']=[(t,ty,sl) for o,t,ty,sl in te]
    out[k]=r
json.dump(out,open('out/feat.json','w'))
print(len(out), sum(1 for r in out.values() if r['xt']))
