import sys
sys.path.insert(0,'/path/to/trudlcport/tools'); sys.path.insert(0,'/path/to/trudlcport/work/crash/B84_r6025')
import io, contextlib
from minidump_read import Minidump
import dump_analyze as D
m=Minidump(sys.argv[1]); H=m.u32(0xc56fdc)
with contextlib.redirect_stdout(io.StringIO()):
    tex=D.walk(m,m.u32(H+4),m.u32(H+0xc),'t')
ids={v[0]:o for o,v in tex.items()}
for t in (259,256,257,258,255,121,1206): print(t, '%08x'%ids[t] if t in ids else 'ASSENTE', D.hexw(m,ids[t],4) if t in ids else '')
print('tot', len(ids))
import json; json.dump(sorted(ids), open('/path/to/trudlcport/work/crash/B88b_r6025/tex_ids_live.json','w'))
mat=None
with contextlib.redirect_stdout(io.StringIO()):
    mat=D.walk(m,m.u32(0x8a6ebc),m.u32(0x8a6ec4),'m')
json.dump(sorted(v[0] for v in mat.values()), open('/path/to/trudlcport/work/crash/B88b_r6025/mat_ids_live.json','w'))
print('2392' , 2392 in {v[0] for v in mat.values()})
