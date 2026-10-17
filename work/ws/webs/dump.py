import sys, struct
sys.path.insert(0,'tools')
import drm_write as DW, drm_reloc as R, material_reslot as MR
def load(p):
    return DW.read(DW.cdrm_decode(open(p,'rb').read(),'le'),'le')
def mat(p,mid):
    D=load(p)
    for s in D.sections:
        if s.type==10 and s.id==mid: return s
if __name__=='__main__':
    for p,mid in [('work/baseline/B8/mods/dlc_caverns_hall.drm',20264),('work/baseline/B8/mods/dlc_caverns_hall.drm',23173),
      ('work/baseline/B8/mods/streamgroups/dlc_dungeonhallb_dungeonhallb_a.drm',23173),('work/baseline/B8/mods/streamgroups/dlc_pillory_pillorymain.drm',20876),
      ('work/baseline/B8/mods/streamgroups/dlc_dungeon_dungeon_main.drm',20264),('work/baseline/B9/mods/dlc_caverns_hall.drm',20264)]:
        s=mat(p,mid); rl=R.parse(s.reloc,'le')
        print(p,mid,len(s.data),'tuple',struct.unpack_from('<4I',s.data,0x28),'x40',struct.unpack_from('<I',s.data,0x40)[0],s.data[0x50:0x54].hex())
        print('  tex',[(t,ty,sl,s.data[o+12],s.data[o+13]) for o,t,ty,sl in MR.tex_entries(s.data,rl,'<')])
        n=struct.unpack_from('<I',s.data,0x58)[0]; po=dict(rl.internal)[0x5C]
        print('  params',[tuple(round(x,3) for x in struct.unpack_from('<4f',s.data,po+16*i)) for i in range(n)])
