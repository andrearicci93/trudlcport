import sys,struct
from capstone import *
D=open('/path/to/trudlcport/work/laa/tru_steam.exe.unpacked.exe','rb').read()
nsec=struct.unpack_from('<H',D,struct.unpack_from('<I',D,0x3c)[0]+6)[0]
pe=struct.unpack_from('<I',D,0x3c)[0]
osz=struct.unpack_from('<H',D,pe+20)[0]
secs=[]
for i in range(nsec):
    o=pe+24+osz+40*i
    vs,va,rs,rp=struct.unpack_from('<IIII',D,o+8)
    secs.append((va,vs,rp,rs))
def off(a):
    r=a-0x400000
    for va,vs,rp,rs in secs:
        if va<=r<va+max(vs,rs): return rp+r-va
def dis(a,n):
    o=off(a); md=Cs(CS_ARCH_X86,CS_MODE_32)
    for i in md.disasm(D[o:o+n],a): print('%x: %s %s'%(i.address,i.mnemonic,i.op_str))
if __name__=='__main__': dis(int(sys.argv[1],16),int(sys.argv[2]))
