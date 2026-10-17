import sys,struct,collections
sys.path.insert(0,'/path/to/trudlcport/tools')
from drm import cdrm_decode, sections_with_data
import terrain_convert as TC, drm_reloc as R
f='/path/to/trudlcport/work/baseline/B11/mods/streamgroups/dlc_water_wheel_waterwheel_main.drm'
raw=cdrm_decode(open(f,'rb').read(),'le'); _,secs=sections_with_data(raw,'le')
texfmt={}
for s in secs:
    if s['type']==5: texfmt[s['id']]=(s['data'][:8],len(s['data']))
sid=int(sys.argv[1]) if len(sys.argv)>1 else 24024
s=[s for s in secs if s['type']==12 and s['id']==sid][0]; d=s['data']; rel=R.parse(s['reloc'],'le'); I=dict(rel.internal)
t=TC.parse(d,'<')
to=I[8]; n=struct.unpack_from('<I',d,to)[0]; tex=struct.unpack_from('<%dI'%n,d,to+4)
mo=I[0xC]; nm=struct.unpack_from('<I',d,mo)[0]; mats=struct.unpack_from('<%dI'%nm,d,mo+4)
print('tex list',n,tex); print('mats',nm,mats)
for k,y in enumerate(t['Y']):
    print(k,'mat',mats[y[0]] if y[0]<nm else y[0],'vb',y[1],'hash',hex(y[2]),y[3:],'A',[tex[i] if 0<=i<n else i for i in (y[6],y[8])])
