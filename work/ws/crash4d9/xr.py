import sys,struct,dsm
va,vs,rp,rs=dsm.secs[0]
code=dsm.D[rp:rp+rs]
t=int(sys.argv[1],16)
for i in range(len(code)-5):
    if code[i] in (0xe8,0xe9):
        d=struct.unpack_from('<i',code,i+1)[0]
        if 0x400000+va+i+5+d==t: print(hex(0x400000+va+i))
# also absolute pointers (vtables/data)
b=struct.pack('<I',t)
import re
for m in re.finditer(re.escape(b),dsm.D): print('ptr@file',hex(m.start()),'va?')
