import sys,struct
from capstone import *
exe=open('/path/to/trudlcport/work/laa/tru_steam.exe.unpacked.exe','rb').read()
# PE sections
pe=struct.unpack_from('<I',exe,0x3c)[0]
ns=struct.unpack_from('<H',exe,pe+6)[0]; so=struct.unpack_from('<H',exe,pe+20)[0]
secs=[]
for i in range(ns):
    o=pe+24+so+40*i
    vs,va,rs,rp=struct.unpack_from('<IIII',exe,o+8); secs.append((va,max(vs,rs),rp))
def rva2off(r):
    for va,s,rp in secs:
        if va<=r<va+s: return rp+r-va
def code(a,n):
    o=rva2off(a-0x400000); return exe[o:o+n]
def dis(a,n,hl=None):
    md=Cs(CS_ARCH_X86,CS_MODE_32)
    for i in md.disasm(code(a,n),a):
        print(('=> ' if i.address==hl else '   ')+'%x: %-24s %s %s'%(i.address,i.bytes.hex(),i.mnemonic,i.op_str))
if __name__=='__main__':
    a=int(sys.argv[1],16);n=int(sys.argv[2],0);dis(a,n,int(sys.argv[3],16) if len(sys.argv)>3 else None)
