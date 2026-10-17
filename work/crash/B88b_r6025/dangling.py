import sys, io, contextlib, collections, json
sys.path.insert(0,'/path/to/trudlcport/tools'); sys.path.insert(0,'/path/to/trudlcport/work/crash/B84_r6025')
from minidump_read import Minidump
import dump_analyze as D
m=Minidump(sys.argv[1]); H=m.u32(0xc56fdc)
with contextlib.redirect_stdout(io.StringIO()):
    tex=D.walk(m,m.u32(H+4),m.u32(H+0xc),'t'); mat=D.walk(m,m.u32(0x8a6ebc),m.u32(0x8a6ec4),'m')
out=collections.defaultdict(list); nrec=0
for obj,(mid,node) in mat.items():
    buf=m.u32(obj+4)
    if not buf: continue
    n50,n51,n52=[m.read(buf+o,1)[0] if m.read(buf+o,1) else None for o in (0x50,0x51,0x52)]
    sl=m.u32(buf+0x54)
    if None in (n50,n51,n52) or not sl: continue
    for i in range(n52+n50):
        r=sl+16*i; q=m.u32(r); b=m.read(r+12,1)
        if q is None: continue
        nrec+=1
        if q==0: continue
        if q not in tex: out[mid].append((i,'%08x'%q,m.u32(q) and '%08x'%m.u32(q)))
print('materiali',len(mat),'rec',nrec,'materiali con puntatori non registrati:',len(out))
for mid,l in sorted(out.items()): print(mid,l)
