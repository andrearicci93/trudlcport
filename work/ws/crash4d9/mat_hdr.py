import sys,struct
sys.path.insert(0,'/path/to/trudlcport/tools')
import drm_write as DW, drm_reloc as R, material_reslot as MR
def mats(path,ids=None):
    D=DW.read(open(path,'rb').read(),'le')
    for s in D.sections:
        if s.type!=10: continue
        if ids and s.id not in ids: continue
        pd=s.data
        es=MR.tex_entries(pd,R.parse(s.reloc,'le'),'<')
        yield s.id,pd[0x50],pd[0x51],pd[0x52],[(e[2],e[3]) for e in es]
if __name__=='__main__':
    ids={int(x) for x in sys.argv[2].split(',')} if len(sys.argv)>2 else None
    for r in mats(sys.argv[1],ids): print(r)
