import sys,struct,collections,pickle
sys.path.insert(0,'tools')
import material_reslot as MR, material_convert as MC
L=MR.libs(); XM,PM=L['XM'],L['PM']
mx2p=pickle.load(open('work/render/material_x2p.pkl','rb'))
rules=pickle.load(open('work/render/param_rules.pkl','rb'))
xd,xr=L['DM'][21210]; t=MC.shader_key(xd); print('xbox tuple',t,'rule?',t in rules, 'nx',struct.unpack_from('>I',xd,0x58)[0])
for xm,(d,r) in XM.items():
    if MC.shader_key(d)==t:
        p=mx2p.get(xm); print(' base xbox',xm,struct.unpack_from('>I',d,0x58)[0],'-> pc',p, struct.unpack_from('<I',PM[p][0],0x58)[0] if p in PM else None)
print([k for k in rules if k[0]==279][:5])
