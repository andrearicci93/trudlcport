import sys,struct,collections
sys.path.insert(0,'/path/to/trudlcport/tools')
import material_reslot as MR, drm_reloc as R
L=MR.libs(); PM=L['PM']
def params(d,r):
    n=struct.unpack_from('<I',d,0x58)[0]; rel=R.parse(r,'le'); o=dict(rel.internal).get(0x5c)
    return [tuple(round(x,2) for x in struct.unpack_from('<4f',d,o+16*i)) for i in range(n)]
tup=tuple(int(x) for x in sys.argv[1:5])
fam=[(k,params(*v)) for k,v in PM.items() if struct.unpack_from('<4I',v[0],0x28)==tup]
print('family',tup,len(fam))
for k,p in fam[:int(sys.argv[5]) if len(sys.argv)>5 else 6]: print(k,len(p),p)
# per-index value ranges
if fam:
    n=len(fam[0][1])
    for i in range(n):
        vs=[f[1][i] for f in fam if len(f[1])>i]
        print(i,'min',tuple(min(v[c] for v in vs) for c in range(4)),'max',tuple(max(v[c] for v in vs) for c in range(4)))
