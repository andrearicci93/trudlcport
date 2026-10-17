import sys,struct,pickle
sys.path.insert(0,'tools')
import drm_write as DW, drm_reloc as R, material_reslot as MR
L=MR.libs(); PM=L['PM']
mx2p=pickle.load(open('work/render/material_x2p.pkl','rb'))
pd,pr=PM[mx2p[4405]]
for f in ('mods_dlc1_rc','mods_current'):
    D=DW.read(open('work/%s/dlc1_uo_bend_switches.drm'%f,'rb').read(),'le')
    for s in D.sections:
        if s.type==10 and s.id==21210:
            d=bytes(s.data); print(f,len(d),len(pd))
            # compare outside params block
            P=dict(R.parse(s.reloc,'le').internal)[0x5C]; Q=dict(R.parse(pr,'le').internal)[0x5C]
            print(' params ptr',hex(P),hex(Q))
            a=d[:P]; b=pd[:Q]; print(' head equal',a==b, [hex(i) for i in range(0,len(a),4) if a[i:i+4]!=b[i:i+4]])
            ta=d[P+160:]; tb=pd[Q+176:]; print(' tail equal',ta==tb,len(ta),len(tb),[hex(i) for i in range(0,min(len(ta),len(tb)),4) if ta[i:i+4]!=tb[i:i+4]][:10])
            ra,rb=R.parse(s.reloc,'le'),R.parse(pr,'le')
            print(' reloc internal',ra.internal[:8],rb.internal[:8]); 
