import sys,struct,json
sys.path.insert(0,'/path/to/trudlcport/tools')
import material_reslot as MR, drm_reloc as R
L=MR.libs(); DM,XM,PM,P=L['DM'],L['XM'],L['PM'],L['P']
mats,msh,mx2p=MR.dlc_tables()
def params(d,r,e):
    n=struct.unpack_from(e+'I',d,0x58)[0]; rel=R.parse(r,'le' if e=='<' else 'be'); o=dict(rel.internal).get(0x5c)
    return [tuple(round(x,3) for x in struct.unpack_from(e+'4f',d,o+16*i)) for i in range(n)]
for m in map(int,sys.argv[1:]):
    v=mats[m]; xd,xr=DM[m]
    print('=== ',m,v['source'],v['flags'],'xt',struct.unpack_from('>4I',xd,0x28),'pt',struct.unpack_from('<4I',v['data'],0x28))
    print(' msh',msh.get(m))
    print(' hdr0x38..',[hex(struct.unpack_from('<I',v['data'],o)[0]) for o in (0x38,0x3c,0x40,0x44,0x48,0x4c,0x50)])
    print(' tex X',[(t,ty,sl) for o,t,ty,sl in MR.tex_entries(xd,R.parse(xr,'be'),'>')],' P',[(t,ty,sl) for o,t,ty,sl in MR.tex_entries(v['data'],R.parse(v['reloc'],'le'),'<')])
    px=params(xd,xr,'>'); pp=params(v['data'],v['reloc'],'<')
    print(' params X',len(px),px); print(' params P',len(pp),pp)
