import sys,struct,capstone
sys.path.insert(0,'/path/to/trudlcport/work/ws/aim')
from xdis import *
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True; md.skipdata=True
a,s,rp,rs=S[0]
d=E[rp:rp+rs]
import re
res=[]
# disassemble linearly in chunks; use sweep
pos=0
want=[(0x18,0x20000000),(0x1c,2)]
out=[]
for ins in md.disasm(d,a):
    if ins.mnemonic in ('or','and','test','xor') and ins.op_str:
        for disp,imm in want:
            if ('+ %#x]'%disp in ins.op_str or '+ 0x%x]'%disp in ins.op_str) and ins.op_str.rstrip().endswith('0x%x'%imm):
                out.append((ins.address,ins.mnemonic,ins.op_str,disp))
for o in out: print('%x %s %s'%o[:3])
print(len(out))
