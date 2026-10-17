"""Scan: PC PS sampler registers (non-engine) with NO texture entry in the material, over installed DLC1 DRMs; calibrate on PC base materials (MR.PM)."""
import sys,struct,collections,pickle
sys.path.insert(0,'/path/to/trudlcport/tools')
from drm import cdrm_decode, sections_with_data
import drm_reloc as R, material_reslot as MR
L=MR.libs(); P=L['P']; PM=L['PM']
def unbound(pd,pr):
    pt=struct.unpack_from('<4I',pd,0x28)
    plibs=[P.get(x) if x else None for x in pt[:3]]
    br=MR.bound_report(pd,pr,plibs,pkeys=[('p',x) for x in pt[:3]])
    return [(r,sorted(ns)[:1]) for r,ns,ty in br if ty is None],pt
if __name__=='__main__':
    # base
    nb=0;bad=[]
    for pid,(pd,pr) in PM.items():
        nb+=1
        try: u,pt=unbound(pd,pr)
        except Exception as e: continue
        if u: bad.append((pid,u))
    print('PC base materials',nb,'with unbound sampler regs:',len(bad)); print(bad[:10])
    rows=[l.rstrip('\n').split('\t') for l in open('/path/to/trudlcport/work/ws/rebuild/installed_effective.tsv')][1:]
    seen={}
    for r in rows:
        if not r[0].endswith('.drm'): continue
        raw=cdrm_decode(open(r[4],'rb').read(),'le'); _,ps=sections_with_data(raw,'le')
        for s in ps:
            if s['type']!=10 or s['id'] in seen: continue
            try: u,pt=unbound(s['data'],s['reloc'])
            except Exception as e: u=None
            seen[s['id']]=(r[0],u,pt)
    print('installed materials',len(seen))
    for k,(f,u,pt) in sorted(seen.items()):
        if u: print(k,f,u,[hex(x) for x in pt])
