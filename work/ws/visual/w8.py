import sys,struct
sys.path.insert(0,'/path/to/trudlcport/tools')
import material_reslot as MR, drm_reloc as R
L=MR.libs(); P=L['P']; PM=L['PM']; DM=L['DM']; X=L['X']; D=L['D']
mats,msh,mx2p=MR.dlc_tables()
def prm(d,r,e):
    n=struct.unpack_from(e+'I',d,0x58)[0]; rel=R.parse(r,'le' if e=='<' else 'be'); o=dict(rel.internal).get(0x5c)
    return [struct.unpack_from(e+'4f',d,o+16*i) for i in range(n)] if o is not None else []
for mid in map(int,sys.argv[1:]):
    m=mats[mid]; d=m['data']; r=m['reloc']; pt=struct.unpack_from('<4I',d,0x28)
    xd,xr=DM[mid]; xt=struct.unpack_from('>4I',xd,0x28)
    print('==',mid,'pc tuple',pt,'xbox tuple',xt,'hdr38',struct.unpack_from('<I',d,0x38)[0], m['source'], msh.get(mid))
    for o,tid,ty,slot in MR.tex_entries(d,R.parse(r,'le'),'<'): print('   tex',tid,'type',ty,'slot',slot)
    for x in MR.bound_report(d,r,[P.get(s) if s else None for s in pt[:3]],[('p',s) for s in pt[:3]]): print('   reg',x)
    for i,(a,b) in enumerate(zip(prm(d,r,'<'),prm(xd,xr,'>'))): print('   p%d'%i,['%.4g'%x for x in a],'|x',['%.4g'%x for x in b])
