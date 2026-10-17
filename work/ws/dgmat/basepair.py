import sys,struct,pickle
sys.path.insert(0,'/path/to/trudlcport/tools')
import material_reslot as MR, drm_reloc as R
L=MR.libs(); XM,PM=L['XM'],L['PM']
mats,msh,mx2p=MR.dlc_tables()
def params(d,r,e):
    n=struct.unpack_from(e+'I',d,0x58)[0]; rel=R.parse(r,'le' if e=='<' else 'be'); o=dict(rel.internal).get(0x5c)
    return [struct.unpack_from(e+'4f',d,o+16*i) for i in range(n)]
tup=(1450,1451,1452,1453)
for xid,(xd,xr) in XM.items():
    if struct.unpack_from('>4I',xd,0x28)==tup:
        p=mx2p.get(xid); print('xbox',xid,'-> pc',p)
        if p in PM:
            xp=params(xd,xr,'>'); pp=params(*PM[p],'<')
            print(' identical params:',xp==pp, 'x0',xp[0],'p0',pp[0],'x1',xp[1],'p1',pp[1])
