import sys,struct,pickle
sys.path.insert(0,'tools')
import material_reslot as MR, material_convert as MC
L=MR.libs(); XM,PM=L['XM'],L['PM']
mx2p=pickle.load(open('work/render/material_x2p.pkl','rb'))
ex=[]
for xm in (4405,12521,12522,18551):
    d,r=XM[xm]; pd,pr=PM[mx2p[xm]]
    ex.append((MC.read_params(d,r,'>'),MC.read_params(pd,pr,'<')))
for j in range(44):
    cand=None
    for x,p in ex:
        fx=[v for q in x for v in q]; pv=p[j//4][j%4]
        c={i for i,v in enumerate(fx) if v==pv}
        cand=c if cand is None else cand&c
    print(j,'p%d.%s'%(j//4,'xyzw'[j%4]),'<-',sorted('x%d.%s'%(i//4,'xyzw'[i%4]) for i in (cand or [])) )
