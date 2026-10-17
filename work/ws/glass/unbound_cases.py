import sys,struct,collections
sys.path.insert(0,'/path/to/trudlcport/tools'); sys.path.insert(0,'/path/to/trudlcport/work/ws/glass')
import drm_reloc as R, material_reslot as MR
from drm import cdrm_decode, sections_with_data
import unbound_scan as U
L=MR.libs(); P=L['P']; NT=MR.name_type()
base='/path/to/trudlcport/work/baseline/B8/mods/'
import os
for dp,dn,fn in os.walk(base):
  for f in sorted(fn):
    if not f.endswith('.drm'): continue
    path=os.path.join(dp,f)
    try: raw=cdrm_decode(open(path,'rb').read(),'le'); _,ps=sections_with_data(raw,'le')
    except Exception: continue
    for s in ps:
        if s['type']!=10: continue
        try: u,pt=U.unbound(s['data'],s['reloc'])
        except Exception: continue
        if not u: continue
        plibs=[P.get(x) if x else None for x in pt[:3]]
        kinds=collections.defaultdict(set)
        for i,lib in enumerate(plibs):
            for r,v in MR.sampler_kinds(lib,('k',)+('p',pt[i])).items(): kinds[r]|=v
        es=MR.tex_entries(s['data'],R.parse(s['reloc'],'le'),'<')
        regs=MR.union_regs(plibs,'p',[('p',x) for x in pt[:3]])
        sampled={r for r,ns in regs.items() if ns-MR.ENGINE}
        print(os.path.relpath(path,base),s['id'],'unbound',[(r,sorted(kinds.get(r,[])),[NT.get(n) for n in regs[r]]) for r,_ in u],'entries',[(tid,ty,sl,'S' if sl in sampled else '-') for o,tid,ty,sl in es])
