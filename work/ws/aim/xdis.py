import sys,struct,capstone
E=open('/path/to/trudlcport/work/laa/tru_steam.exe.unpacked.exe','rb').read()
pe=struct.unpack_from('<I',E,0x3c)[0]; ns=struct.unpack_from('<H',E,pe+6)[0]; ob=struct.unpack_from('<H',E,pe+20)[0]
base=struct.unpack_from('<I',E,pe+0x34)[0]
S=[]
for i in range(ns):
    o=pe+24+ob+40*i; vs,va,rs,rp=struct.unpack_from('<IIII',E,o+8)
    S.append((va+base,max(vs,rs),rp,rs))
def rd(va,n):
    for a,s,rp,rs in S:
        if a<=va<a+s: return E[rp+va-a:rp+va-a+n]
    return b'\0'*n
def dis(va,n=0x100):
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
    for i in md.disasm(rd(va,n),va): print('%x: %s %s'%(i.address,i.mnemonic,i.op_str))
if __name__=='__main__': dis(int(sys.argv[1],16),int(sys.argv[2],0) if len(sys.argv)>2 else 0x100)
