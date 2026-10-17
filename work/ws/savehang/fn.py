import sys,capstone,pefile
data=open('work/laa/tru_steam.exe.unpacked.exe','rb').read()
pe=pefile.PE('work/laa/tru_steam.exe.unpacked.exe')
def rd(va,n):
    rva=va-0x400000
    for s in pe.sections:
        if s.VirtualAddress<=rva<s.VirtualAddress+s.SizeOfRawData:
            o=s.PointerToRawData+rva-s.VirtualAddress; return data[o:o+n]
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
a=int(sys.argv[1],16); n=int(sys.argv[2],16)
for i in md.disasm(rd(a,n),a): print(hex(i.address),i.mnemonic,i.op_str)
