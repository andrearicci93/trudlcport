import sys,os,struct,pickle
sys.path.insert(0,'tools')
import material_reslot as MR, drm_reloc as R
L=MR.libs(); X,D,P,PM,DM=L['X'],L['D'],L['P'],L['PM'],L['DM']
mats,msh,mx2p=MR.dlc_tables()
mid=21164
m=mats[mid]; print(m['source'],m['flags'],m.get('pc_tuple'),msh.get(mid))
pd,pr=m['data'],m['reloc']
xd,xr=DM[mid]
print('xbox entries',[(hex(o),hex(t),ty,s) for o,t,ty,s in MR.tex_entries(xd,R.parse(xr,'be'),'>')])
print('pc  entries',[(hex(o),hex(t),ty,s) for o,t,ty,s in MR.tex_entries(pd,R.parse(pr,'le'),'<')])
nd,ch=MR.dlc_reslot(mid,pd,pr)
print('reslot now',ch)
print('diffs',[hex(i) for i in range(0,len(pd),4) if pd[i:i+4]!=nd[i:i+4]])
xt=struct.unpack_from('>4I',xd,0x28); pt=struct.unpack_from('<4I',pd,0x28); print(xt,pt)
XL=lambda s: D.get(s,X.get(s)) if s else None
for i in range(3):
  print('pass',i,'x',xt[i],'p',pt[i], 'xregs',MR.regmap(XL(xt[i]),'x') if xt[i] else None,'\n    pregs',MR.regmap(P.get(pt[i]),'p') if pt[i] else None)
bm=msh[mid]['base_material']; print('base',bm, mx2p.get(bm))
if bm in L['XM']:
  bd,br=L['XM'][bm]; print('base xbox tuple',struct.unpack_from('>4I',bd,0x28),[(ty,s) for o,t,ty,s in MR.tex_entries(bd,R.parse(br,'be'),'>')])
  pb=PM[mx2p[bm]]; print('base pc tuple',struct.unpack_from('<4I',pb[0],0x28),[(hex(t),ty,s) for o,t,ty,s in MR.tex_entries(pb[0],R.parse(pb[1],'le'),'<')])
for k,f in (('gw','mods_current/dlc1_ei_grapple_wall.drm'),('ds','mods_fix20/dlc1_uo_dragon_slider.drm')):
  import drm_write as DW
  Dr=DW.read(open('work/'+f,'rb').read(),'le')
  for s in Dr.sections:
    if s.type==10 and s.id==mid: print(k,[(hex(t),ty,sl) for o,t,ty,sl in MR.tex_entries(bytes(s.data),R.parse(s.reloc,'le'),'<')])
