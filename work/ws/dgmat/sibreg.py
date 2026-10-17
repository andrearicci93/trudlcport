import sys,struct
sys.path.insert(0,'/path/to/trudlcport/tools')
import material_reslot as MR, drm_reloc as R
L=MR.libs(); PM,P=L['PM'],L['P']
tup=(0,262,263)
plibs=[P.get(x) if x else None for x in tup]
regs=MR.union_regs(plibs,'p',[('p',x) for x in tup])
print({r:[n[-28:] for n in sorted(ns)] for r,ns in sorted(regs.items())})
kinds={}
for i,l in enumerate(plibs):
    if l and l['kind']==1:
        for r,v in MR.sampler_kinds(l,('k','p',tup[i])).items(): kinds.setdefault(r,set()).update(v)
print(kinds)
for b,(bd,br) in PM.items():
    if struct.unpack_from('<4I',bd,0x28)[:3]==tup:
        print(b,sorted((sl,t,ty) for o,t,ty,sl in MR.tex_entries(bd,R.parse(br,'le'),'<')))
# per-permutation sampler use
from shaderlib import constants
for x in tup[1:]:
    for s in sorted(set(P[x]['slots'])-{0xFFFFFFFF}):
        v,c=constants(P[x]['entries'][s]['blob'],'p'); print(x,hex(s),sorted((ri,n[-14:]) for n,rs,ri,rc in c if rs==3 and 'Sampler' not in n))
