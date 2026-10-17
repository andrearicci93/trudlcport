import sys,struct
sys.path.insert(0,'/path/to/trudlcport/tools')
import material_reslot as MR, drm_reloc as R
L=MR.libs(); PM=L['PM']; DM=L['DM']
def params(d,r,e):
    n=struct.unpack_from(e+'I',d,0x58)[0]; rel=R.parse(r,'le' if e=='<' else 'be'); o=dict(rel.internal).get(0x5c)
    return [struct.unpack_from(e+'4f',d,o+16*i) for i in range(n)]
print(list(DM)[:3], 15297 in DM, 10918 in PM)
xd,xr=DM[15297]; print(xd[:0x58].hex()); 
for i,v in enumerate(params(xd,xr,'>')): print(i,['%.4g'%x for x in v])
