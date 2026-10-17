import sys;sys.path.insert(0,'.')
import dm,struct
a0=int(sys.argv[1],16);n=int(sys.argv[2],0)
for a in range(a0,a0+n,16):
    b=dm.rd(a,16)
    if not b: print(hex(a),'--');continue
    print(hex(a),' '.join('%08x'%x for x in struct.unpack('<4I',b)))
