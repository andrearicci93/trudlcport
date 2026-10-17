"""Regola tipizzata: materiale con PS che campiona BackBuffer+DepthBuffer+Normal (acqua a rifrazione) -> header 0x38 = valore base PC (0, 1/1 sul base: 10918).
Selftest: sui 2248 materiali base PC 0 modifiche. Applica a tutti i DRM di una baseline (solo sezioni tipo 10)."""
import sys,os,struct
sys.path.insert(0,'/path/to/trudlcport/tools')
import material_reslot as MR, drm_write as DW
L=MR.libs(); P=L['P']; PM=L['PM']
def water(d):
    pt=struct.unpack_from('<4I',d,0x28)
    regs=MR.union_regs([P.get(s) if s else None for s in pt[:3]],'p',keys=[('p',s) for s in pt[:3]])
    n=set().union(*regs.values()) if regs else set()
    return any('BackBuffer' in x for x in n) and any('Depth' in x for x in n) and any('Normal' in x for x in n)
def fix(d):
    if water(d) and struct.unpack_from('<I',d,0x38)[0]!=0:
        b=bytearray(d); struct.pack_into('<I',b,0x38,0); return bytes(b)
    return d
if __name__=='__main__':
    ch=sum(1 for k,(d,r) in PM.items() if fix(d)!=d); print('selftest base PC: sezioni cambiate',ch,'su',len(PM))
    src,out=sys.argv[1:3]
    D=DW.read(open(src,'rb').read(),'le'); n=[]
    for s in D.sections:
        if s.type==10:
            nd=fix(s.data)
            if nd!=s.data: s.data=nd; n.append(s.id)
    if n:
        open(out,'wb').write(DW.cdrm_encode(D.write('le'),'le')); print(os.path.basename(src),'mats',n)
