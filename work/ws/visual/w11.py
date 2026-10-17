import sys,struct,collections
sys.path.insert(0,'/path/to/trudlcport/tools')
import material_reslot as MR, drm_reloc as R
L=MR.libs(); P=L['P']; PM=L['PM']
NT=MR.name_type()
def mism(d,r):
    pt=struct.unpack_from('<4I',d,0x28)
    plibs=[P.get(s) if s else None for s in pt[:3]]; pk=[('p',s) for s in pt[:3]]
    regs=MR.union_regs(plibs,'p',keys=pk)
    out=[]
    for o,tid,ty,slot in MR.tex_entries(d,R.parse(r,'le'),'<'):
        for n in regs.get(slot,()):
            if n in MR.ENGINE: continue
            if n in NT and NT[n]!=ty: out.append((tid,ty,slot,n[-40:],NT[n]))
    return out
nb=0;tot=0
for k,(d,r) in PM.items():
    tot+=1
    if mism(d,r): nb+=1
print('base PC materials with name-type mismatch',nb,'/',tot)
mats,msh,mx2p=MR.dlc_tables()
res={}
for k,m in mats.items():
    if m['source']!='converted': continue
    mm=mism(m['data'],m['reloc'])
    if mm: res[k]=mm
print('DLC converted with mismatch',len(res),'/',sum(1 for m in mats.values() if m['source']=='converted'))
for k,v in list(res.items())[:60]: print(k,v[:3])
