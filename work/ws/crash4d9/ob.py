from dm import *
o=0x18861db0
b=rd(o,0x80); print(b.hex())
print(rd(o-0x40,0x40).hex())
sp=0x1af990
for i in range(8): print(hex(sp+4*i),hex(u32(sp+4*i)))
bp=sp
for _ in range(8):
    n=u32(bp); r=u32(bp+4); print('frame',hex(bp),'ret',hex(r)); 
    if not n or n<bp: break
    bp=n
