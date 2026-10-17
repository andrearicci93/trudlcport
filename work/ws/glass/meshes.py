import sys,struct,pickle
sys.path.insert(0,'/path/to/trudlcport/tools')
from drm import cdrm_decode, sections_with_data
import drm_reloc as R
Rt='/path/to/trudlcport/work/mods_dlc1_rc/'
tex=pickle.load(open('tex_table.pkl','rb'))
for f in sys.argv[1:]:
    raw=cdrm_decode(open(f,'rb').read(),'le'); _,secs=sections_with_data(raw,'le')
    for s in secs:
        if s['type']!=12: continue
        rel=R.parse(s['reloc'],'le')
        ts=[];ms=[]
        for t,o in sorted(rel.idref+rel.idref_a,key=lambda x:x[1]):
            v=struct.unpack_from('<I',s['data'],o)[0]
            (ts if t==5 else ms if t==10 else []).append(v)
        print(f,s['id'],len(s['data']),'tex',ts,'mat',ms)
