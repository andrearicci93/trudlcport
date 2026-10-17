import sys; sys.path.insert(0,'/path/to/trudlcport/work/ws/xexre')
import x
va=int(sys.argv[1],16); n=int(sys.argv[2])
for k in range(n):
    a=va+4*k
    r=list(x.md.disasm(x.D[a-x.BASE:a-x.BASE+4],a))
    print('%08x  %s'%(a,(r[0].mnemonic+' '+r[0].op_str) if r else '.long %08x'%x.u32(a)))
