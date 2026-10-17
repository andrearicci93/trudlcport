"""Riferimenti u32 ai 5 uid intro rimappati +20000: PC (B87) vs Xbox vergine, per (DRM, sezione id, offset). Salva uid_refs.json."""
import sys,os,struct,json,glob,collections
T='/path/to/trudlcport/tools'; sys.path.insert(0,T)
import drm
from archive import Archive
from names import load,L
R='/path/to/trudlcport/work/baseline/B87_materiali19/mods/'
PAIRS={9392:29392,9397:29397,9395:29395,9396:29396,6713:26713}
TYPES_OK={0,7,8}   # general, DTP, script (le texture/shader/wave non portano id)
def scan(secs,E,vals,drmname):
    out=collections.defaultdict(list)
    for s in secs:
        if s['type'] not in TYPES_OK or not s['data']: continue
        d=s['data']
        for v in vals:
            pat=struct.pack(E+'I',v); i=-1
            while True:
                i=d.find(pat,i+1)
                if i<0: break
                if i%4==0: out[(drmname,s['type'],s['id'],i)].append(v)
    return out
pc={}
for p in sorted(glob.glob(R+'**/*.drm',recursive=True)):
    try: sc=drm.sections_with_data(drm.cdrm_decode(open(p,'rb').read(),'le'),'le')[1]
    except Exception: continue
    for k,v in scan(sc,'<',PAIRS.values(),os.path.relpath(p,R)).items(): pc[k]=v
xb={}
C='/path/to/Xenia-SteveRepack/Content/534307EC/00000002/'; xn=load(L+'Tomb Raider Underworld (Xenon).txt')
for pk in [C+'9CA70CF0EDA43654D158C2E37470D301DFA850E753/pack10.000',C+'600A12643FCDAC84003E6E0DBD0A1A8F7DAE9DD153/pack11.000']:
    A=Archive(pk,'be')
    for r in A.idx:
        nm=xn.get(r['hash'],'0x%08x'%r['hash']).split('\\')[-1]
        f=A.read(r)
        if f[:4] not in (b'CDRM',b'\0\0\0\x13'): continue
        try: sc=drm.sections_with_data(drm.cdrm_decode(f,'be'),'be')[1]
        except Exception: continue
        for k,v in scan(sc,'>',PAIRS.keys(),nm).items(): xb[k]=v
print('PC hit',len(pc),'Xbox hit',len(xb))
inv={v:k for k,v in PAIRS.items()}
match=0;pc_only=[];xb_only=[]
for k,v in pc.items():
    old=[inv[x] for x in v]
    key=k
    # nome DRM Xbox puo' differire (.drm); confronto per (basename, type, id, off)
    kk=(os.path.basename(k[0]),)+k[1:]
    cand=[xk for xk in xb if (os.path.basename(xk[0]),)+xk[1:]==kk]
    if cand and xb[cand[0]]==old: match+=1
    else: pc_only.append((k,v))
for k,v in xb.items():
    kk=(os.path.basename(k[0]),)+k[1:]
    if not any((os.path.basename(pk[0]),)+pk[1:]==kk for pk in pc): xb_only.append((k,v))
print('combaciano',match,'solo PC',len(pc_only),'solo Xbox',len(xb_only))
print('SOLO PC:',pc_only[:30]); print('SOLO XBOX:',xb_only[:30])
json.dump(dict(pc=[(list(k),v) for k,v in pc.items()],xb=[(list(k),v) for k,v in xb.items()]),open('/path/to/trudlcport/work/ws/giro5/uid_refs.json','w'))
