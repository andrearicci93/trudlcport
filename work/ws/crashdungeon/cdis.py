import capstone,sys,pefile
exe=open('/path/to/trudlcport/work/laa/tru_steam.exe.unpacked.exe','rb').read()
pe=pefile.PE(data=exe)
def rd(va,n):
    rva=va-0x400000
    for s in pe.sections:
        if s.VirtualAddress<=rva<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData):
            o=s.PointerToRawData+rva-s.VirtualAddress; return exe[o:o+n]
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
def dis(va,n=0x60,stop_ret=True):
    for i in md.disasm(rd(va,n),va):
        print(hex(i.address),i.mnemonic,i.op_str)
        if stop_ret and i.mnemonic=='ret': break
if __name__=='__main__':
    for a in sys.argv[1:]:
        print('---',a); dis(int(a,16),0x100)
