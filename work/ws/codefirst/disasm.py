import sys,pefile,capstone
pe=pefile.PE('/path/to/trudlcport/work/laa/tru_steam.exe.unpacked.exe')
base=pe.OPTIONAL_HEADER.ImageBase
def rd(va,n):
    return pe.get_data(va-base,n)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
for a in sys.argv[1:]:
    va,n=a.split(':'); va=int(va,16); n=int(n,0)
    for i in md.disasm(rd(va,n),va): print(f'{i.address:08x}  {i.mnemonic} {i.op_str}')
    print('---')
