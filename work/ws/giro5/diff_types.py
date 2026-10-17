"""Per ogni DRM diverso fra due baseline: conteggio sezioni cambiate per tipo. Uso: diff_types.py BASE_A BASE_B"""
import sys,os,hashlib,collections
sys.path.insert(0,'/path/to/trudlcport/tools')
from drm import cdrm_decode, sections_with_data
R='/path/to/trudlcport/work/baseline/'
A,B=sys.argv[1],sys.argv[2]
def md(b):
    d={}
    for r,_,fs in os.walk(R+b+'/mods'):
        for f in fs:
            p=os.path.join(r,f)
            if p.endswith('.drm'): d[os.path.relpath(p,R+b+'/mods')]=p
    return d
da,db=md(A),md(B)
for k in sorted(da):
    if k not in db: continue
    a=open(da[k],'rb').read(); b=open(db[k],'rb').read()
    if a==b: continue
    try:
        ha,sa=sections_with_data(cdrm_decode(a,'le'),'le'); hb,sb=sections_with_data(cdrm_decode(b,'le'),'le')
    except Exception as e:
        print(k,'ERR',e); continue
    ch=collections.Counter()
    if len(sa)!=len(sb): print(k,'N sez',len(sa),len(sb))
    for x,y in zip(sa,sb):
        if x['data']!=y['data'] or x['reloc']!=y['reloc'] or x['size']!=y['size']: ch[x['type']]+=1
    print(k,dict(ch))
