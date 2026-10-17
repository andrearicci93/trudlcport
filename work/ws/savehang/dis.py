import sys,capstone
from minidump.minidumpfile import MinidumpFile
m=MinidumpFile.parse('work/crash/save_hang.dmp'); rd=m.get_reader()
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
a=int(sys.argv[1],16); n=int(sys.argv[2],16) if len(sys.argv)>2 else 0x100
code=rd.read(a,n)
for i in md.disasm(code,a): print(hex(i.address),i.mnemonic,i.op_str)
