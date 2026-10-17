"""Scansione Intro.uniqueID di tutte le unita' del PC base (bigfile.000). Salva work/ws/giro5/base_uids.json {drm_hash: [uids]}."""
import sys,os,struct,json,time
T='/path/to/trudlcport/tools'; sys.path.insert(0,T)
import drm, unit_ids as U
from archive import Archive
A=Archive('/path/to/trudlcport/pc/bigfile.000','le')
out={}; t0=time.time(); n=0
for r in A.idx:
    try:
        f=A.read(r)
        if f[:4]!=b'CDRM' and f[:4]!=b'\0\0\0\x13' and f[:4]!=b'\x13\0\0\0': continue
        sc=drm.sections_with_data(drm.cdrm_decode(f,'le'),'le')[1]
        Lv=U.level_info(sc,'le')
    except Exception: continue
    n+=1
    if not Lv or not Lv['intros']: continue
    ids=[struct.unpack_from('<I',sc[si]['data'],o+0x58)[0] for si,o in Lv['intros']]
    out['%08x_%d'%(r['hash'],r['spec'])]=ids
print('drm letti',n,'unita',len(out),'sec',time.time()-t0)
allu=[u for v in out.values() for u in v]
print('totale intro',len(allu),'max',max(allu),'>=16352:',sum(u>=16352 for u in allu),'distinti',len(set(allu)))
json.dump(out,open('/path/to/trudlcport/work/ws/giro5/base_uids.json','w'))
