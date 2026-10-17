import sys,struct,collections,re
sys.path.insert(0,'/path/to/trudlcport/tools')
import material_reslot as MR, drm_reloc as R
L=MR.libs(); PM,P=L['PM'],L['P']
mats,msh,mx2p=MR.dlc_tables()
cases={20530:(9837,[2,5]),22581:(9837,[2,5]),21199:(11578,None),21537:(None,None),23814:(None,None),21185:(None,None),23211:(None,None),20346:(None,None),23173:(None,None)}
import json
C=json.load(open('out/census.json'))
from drm import cdrm_decode, sections_with_data
T='/path/to/trudlcport/work/baseline/B8/mods/'
def load(mid):
    drm=sorted(C[str(mid)]['drm'])[0]
    raw=cdrm_decode(open(T+drm.replace('\\','/'),'rb').read(),'le'); _,secs=sections_with_data(raw,'le')
    for s in secs:
        if s['type']==10 and s['id']==mid: return s['data'],s['reloc']
sys.path.insert(0,'/path/to/trudlcport/tools')
import unbound_fix as U
for mid in cases:
    pd,pr=load(mid); u,pt=U.unbound(pd,pr)
    print('=====',mid,'pt',pt,'unbound',[(r,[n[-34:] for n in ns],k) for r,ns,k in u],'bm',msh.get(mid,{}).get('base_material'))
    sib=[b for b,(bd,br) in PM.items() if struct.unpack_from('<4I',bd,0x28)[:3]==tuple(pt[:3])]
    # looser: sharing the pass-2 lib
    sib2=[b for b,(bd,br) in PM.items() if struct.unpack_from('<4I',bd,0x28)[2]==pt[2]] 
    for r,ns,k in u:
        for nm,S in (('same tuple',sib),('same pass2 lib',sib2)):
            c=collections.Counter()
            for b in S:
                bd,br=PM[b]
                for o,t,ty,sl in MR.tex_entries(bd,R.parse(br,'le'),'<'):
                    if sl==r: c[(t,ty)]+=1
            print('  reg',r,nm,'n=%d'%len(S),c.most_common(5))
