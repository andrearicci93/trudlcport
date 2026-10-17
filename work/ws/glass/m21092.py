import sys,struct,pickle
sys.path.insert(0,'/path/to/trudlcport/tools')
import drm_reloc as R, material_reslot as MR
L=MR.libs(); DM=L['DM']; PM=L['PM']
xd,xr=DM[21092]
import binascii
print('XBOX len',len(xd)); 
print(struct.unpack_from('>16I',xd,0))
print(struct.unpack_from('>4I',xd,0x28))
rel=R.parse(xr,'be'); print(MR.tex_entries(xd,rel,'>'))
for o in range(0,len(xd),16): print('%04x'%o, xd[o:o+16].hex())
mats=pickle.load(open('/path/to/trudlcport/work/render/dlc_materials_pc.pkl','rb'))
pd=mats[21092]['data']
print('PC len',len(pd))
for o in range(0,len(pd),16): print('%04x'%o, pd[o:o+16].hex())
