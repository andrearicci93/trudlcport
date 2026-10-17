import sys,struct,collections
sys.path.insert(0,'/path/to/trudlcport/tools')
import material_reslot as MR
L=MR.libs(); PM=L['PM']; XM=L['XM']; DM=L['DM']
c=collections.Counter(); 
for k,(d,r) in PM.items(): c[struct.unpack_from('<I',d,0x38)[0]]+=1
print('PC base 0x38',c)
c=collections.Counter()
for k,(d,r) in XM.items(): c[struct.unpack_from('>I',d,0x38)[0]]+=1
print('Xbox base 0x38',c)
c=collections.Counter()
for k,(d,r) in DM.items(): c[struct.unpack_from('>I',d,0x38)[0]]+=1
print('Xbox DLC 0x38',c)
# which base PC have 4
print([k for k,(d,r) in PM.items() if struct.unpack_from('<I',d,0x38)[0]!=0][:20])
print([ (k,struct.unpack_from('>4I',d,0x28)) for k,(d,r) in DM.items() if struct.unpack_from('>I',d,0x38)[0]==4][:20])
