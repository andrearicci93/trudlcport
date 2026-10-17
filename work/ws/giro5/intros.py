"""Elenco Intro (oggetti istanziati) di una unita': PC (baseline) e Xbox vergine (pack10/11). Uso: intros.py NOME_DRM [filtro_nome_oggetto ...]
Campi Intro (0x90 B): +0x50 u16 objectID, +0x58 u32 uniqueID; posizione (float x,y,z) cercata a +0x00.. (stampa raw)."""
import sys,os,struct
T='/path/to/trudlcport/tools'; sys.path.insert(0,T)
import drm, drm_write as DW, unit_ids as U
from archive import Archive
from names import load, L
R='/path/to/trudlcport/work/baseline/'
def objnames(path):
    d={}
    for l in open(path,errors='ignore'):
        p=l.strip().split(',',1)
        if len(p)==2 and p[0].isdigit(): d[int(p[0])]=p[1]
    return d
def pc_intros(base,name):
    sc=drm.sections_with_data(drm.cdrm_decode(open(R+base+'/mods/'+name,'rb').read(),'le'),'le')[1]
    Lv=U.level_info(sc,'le'); out=[]
    for si,o in Lv['intros']:
        d=sc[si]['data']; out.append(dict(off=(si,o),uid=struct.unpack_from('<I',d,o+0x58)[0],obj=struct.unpack_from('<H',d,o+0x50)[0],raw=bytes(d[o:o+0x90])))
    return out
_xb={}
def xbox_intros(name):
    C='/path/to/Xenia-SteveRepack/Content/534307EC/00000002/'
    xn=load(L+'Tomb Raider Underworld (Xenon).txt')
    for pk in [C+'9CA70CF0EDA43654D158C2E37470D301DFA850E753/pack10.000',C+'600A12643FCDAC84003E6E0DBD0A1A8F7DAE9DD153/pack11.000']:
        A=Archive(pk,'be')
        for r in A.idx:
            n=xn.get(r['hash'],'').split('\\')[-1]
            if n==name:
                raw=drm.cdrm_decode(A.read(r),'be'); sc=drm.sections_with_data(raw,'be')[1]
                Lv=U.level_info(sc,'be'); out=[]
                for si,o in Lv['intros']:
                    d=sc[si]['data']; out.append(dict(off=(si,o),uid=struct.unpack_from('>I',d,o+0x58)[0],obj=struct.unpack_from('>H',d,o+0x50)[0],raw=bytes(d[o:o+0x90])))
                return out
if __name__=='__main__':
    name=sys.argv[1]; flt=sys.argv[2:]
    pcn=objnames(R+'B87_materiali19/mods/tr8/pc-w/objectlist.txt'); xbn=objnames('/path/to/trudlcport/work/dlc1/objectlist.txt')
    for base in ('B11','B45','B87_materiali19'):
        I=pc_intros(base,name); print('==',base,name,len(I),'intro')
        for i in I:
            nm=pcn.get(i['obj'],'?')
            if not flt or any(f in nm for f in flt): print('  uid',i['uid'],'obj',i['obj'],nm, struct.unpack_from('<3f',i['raw'],0x30))
    I=xbox_intros(name)
    if I is None: print('Xbox: non trovato')
    else:
        print('== Xbox vergine',len(I),'intro')
        for i in I:
            nm=xbn.get(i['obj'],'?')
            if not flt or any(f in nm for f in flt): print('  uid',i['uid'],'obj',i['obj'],nm, struct.unpack_from('>3f',i['raw'],0x30))
