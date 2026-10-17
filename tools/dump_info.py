"""Crash dump summary for tru.exe: python dump_info.py file.dmp"""
import sys, struct, capstone
from minidump.minidumpfile import MinidumpFile
m = MinidumpFile.parse(sys.argv[1]); er = m.exception.exception_records[0]; rec = er.ExceptionRecord
print('code', rec.ExceptionCode, 'addr', hex(rec.ExceptionAddress), 'info', [hex(x) for x in rec.ExceptionInformation[:2]])
loc = er.ThreadContext
raw = open(sys.argv[1], 'rb').read()[loc.Rva:loc.Rva + loc.DataSize]
f = lambda o: struct.unpack_from('<I', raw, o)[0]
R = dict(Edi=f(156), Esi=f(160), Ebx=f(164), Edx=f(168), Ecx=f(172), Eax=f(176), Ebp=f(180), Eip=f(184), Esp=f(196))
print({k: hex(v) for k, v in R.items()})
rd = m.get_reader()
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
try:
    code = rd.read(R['Eip'] - 0x20, 0x50)
    for i in md.disasm(code, R['Eip'] - 0x20): print(('=> ' if i.address == R['Eip'] else '   ') + hex(i.address), i.mnemonic, i.op_str)
except Exception as e: print('code read fail', e)
try:
    st = rd.read(R['Esp'], 0x300)
    print('stack ret candidates:', [(hex(R['Esp'] + k), hex(struct.unpack_from('<I', st, k)[0])) for k in range(0, len(st), 4) if 0x401000 <= struct.unpack_from('<I', st, k)[0] < 0x43e000 + 0x400000][:10])
except Exception as e: print('stack read fail', e)
