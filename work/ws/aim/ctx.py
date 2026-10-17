import sys,struct,capstone
from xdis import *
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
for t in sys.argv[1:]:
    va=int(t,16)
    # disasm from a bit before; try to align by starting 0x18 earlier
    best=None
    for st in range(va-0x20,va-4):
        ins=list(md.disasm(rd(st,0x60),st))
        if any(i.address==va-2 or i.address==va-1 or i.address==va for i in ins) and ins:
            best=ins;break
    print('=== %s'%t)
    for i in best[:16]: print('  %x: %s %s'%(i.address,i.mnemonic,i.op_str))
