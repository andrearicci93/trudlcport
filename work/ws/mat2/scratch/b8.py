import sys,struct,pickle
sys.path.insert(0,'tools')
import material_reslot as MR, material_convert as MC, drm_reloc as R
L=MR.libs(); XM,PM,DM=L['XM'],L['PM'],L['DM']
mx2p=pickle.load(open('work/render/material_x2p.pkl','rb'))
def prm(d,r,e): return MC.read_params(d,r,e)
for xm in (4405,12521,12522,18551,'dlc'):
    if xm=='dlc': d,r=DM[21210]; vx=prm(d,r,'>'); vp=None
    else:
        d,r=XM[xm]; vx=prm(d,r,'>'); pd,pr=PM[mx2p[xm]]; vp=prm(pd,pr,'<')
    print(xm); 
    for i,v in enumerate(vx): print('  x',i,['%.4g'%a for a in v], ('   p %s'%['%.4g'%a for a in vp[i]]) if vp and i<len(vp) else '')
    if vp: print('  p',len(vp)-1,['%.4g'%a for a in vp[-1]])
