import sys,struct,collections,json
sys.path.insert(0,'/path/to/trudlcport/tools')
import material_reslot as MR, drm_reloc as R, unbound_fix as U
from drm import cdrm_decode, sections_with_data
L=MR.libs(); P,DM,X,D=L['P'],L['DM'],L['X'],L['D']
C=json.load(open('out/census.json'))
T='/path/to/trudlcport/work/baseline/B8/mods/'
nt=MR.name_type()
def load(mid):
    drm=sorted(C[str(mid)]['drm'])[0]
    raw=cdrm_decode(open(T+drm.replace('\\','/'),'rb').read(),'le'); _,secs=sections_with_data(raw,'le')
    for s in secs:
        if s['type']==10 and s['id']==mid: return s['data'],s['reloc']
for mid in [20530,22581,21199,21537,23814,21185,23211,20346,23173]:
    pd,pr=load(mid); pt=struct.unpack_from('<4I',pd,0x28)
    plibs=[P.get(x) if x else None for x in pt[:3]]; keys=[('p',x) for x in pt[:3]]
    regs=MR.union_regs(plibs,'p',keys)
    pe=[(t,ty,sl) for o,t,ty,sl in MR.tex_entries(pd,R.parse(pr,'le'),'<')]
    xd,xr=DM[mid]; xt=struct.unpack_from('>4I',xd,0x28); xe=[(t,ty,sl) for o,t,ty,sl in MR.tex_entries(xd,R.parse(xr,'be'),'>')]
    xlibs=[ (D.get(x) or X.get(x)) if x else None for x in xt[:3]]
    xregs=MR.union_regs(xlibs,'x',[('x',x) for x in xt[:3]])
    print('====',mid)
    print(' PC regs:',{r:sorted(n[-30:] for n in ns)[:2] for r,ns in regs.items() if r<20})
    print(' PC entries (tid,ty,slot):',pe)
    print(' XB regs:',{r:sorted(n[-30:] for n in ns)[:2] for r,ns in xregs.items()})
    print(' XB entries:',xe)
