"""lista istanze (layout B263 list2) di un dump qualsiasi, filtro per nome. uso: list_any.py DUMP [regex]"""
import sys,struct,re
sys.path.insert(0,'/path/to/trudlcport/tools')
from minidump_read import Minidump
m=Minidump(sys.argv[1]); rx=re.compile(sys.argv[2] if len(sys.argv)>2 else '.')
names={}
for l in open('/path/to/trudlcport/work/baseline/B279_unitcurve/mods/tr8/pc-w/objectlist.txt',errors='ignore'):
    p=l.split(',',1)
    if len(p)==2 and p[0].strip().isdigit(): names[int(p[0])]=p[1].strip()
pl=m.u32(0xe7f094); i=m.u32(0xd98d54); n=0
while i and n<5000:
    n+=1; b=m.read(i,0x2f0)
    if b is None: break
    w=struct.unpack('<188I',b); f=struct.unpack('<188f',b)
    oid=m.u32(w[4]+0x14) if w[4] else -1; nm=names.get(oid,'?')
    if rx.search(nm) or i==pl: print('%08x %4d %-28s uid=%10d pos=(%8.1f %8.1f %8.1f) f14=%08x f18=%08x fa0=%08x %s'%(i,oid,nm[:28],w[0x16],f[8],f[9],f[10],w[5],w[6],w[0x28],'PLAYER' if i==pl else ''))
    i=w[2]
