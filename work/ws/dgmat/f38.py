import sys,struct,collections
sys.path.insert(0,'/path/to/trudlcport/tools')
import material_reslot as MR
L=MR.libs(); PM,XM=L['PM'],L['XM']; mats,msh,mx2p=MR.dlc_tables()
c=collections.Counter(); pair=collections.Counter()
for k,(d,r) in PM.items(): c[struct.unpack_from('<I',d,0x38)[0]]+=1
print('PC base u32@0x38',c.most_common(8))
for x,p in mx2p.items():
    if x in XM and p in PM: pair[(struct.unpack_from('>I',XM[x][0],0x38)[0],struct.unpack_from('<I',PM[p][0],0x38)[0])]+=1
print('pairs (xbox,pc)',pair.most_common(10))
# header words 0x30..0x58 on all
for off in (0x2c,0x3c,0x40,0x44,0x48,0x4c,0x50,0x54,0x58,0x5c):
    cc=collections.Counter(struct.unpack_from('<I',d,off)[0] for d,r in PM.values()); print(hex(off),cc.most_common(4))
