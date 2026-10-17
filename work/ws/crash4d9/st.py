from dm import *
import struct
tid,code,addr,info,c=exc(); r=regs(c)
print('main-stack check, esp',hex(r['Esp']), rd(r['Esp'],4) is not None)
sp=r['Esp']
for i in range(0,64):
    v=u32(sp+4*i)
    flag=''
    if v and 0x401000<=v<0x800000: flag=' <code?'
    print(hex(sp+4*i),hex(v) if v is not None else None,flag)
