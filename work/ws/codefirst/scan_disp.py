"""Scansione .text: istruzioni con operando memoria [reg+disp] per disp nel range dato. Uso: scan_disp.py LO HI -> righe addr mnem ops"""
import sys,pefile,capstone,re,pickle,os
lo,hi=int(sys.argv[1],16),int(sys.argv[2],16)
pe=pefile.PE('/path/to/trudlcport/work/laa/tru_steam.exe.unpacked.exe')
t=pe.get_data(0x1000,0x43d000); md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.skipdata=True
rx=re.compile(r'\[(?:\w+ \+ )?(?:\w+\*\d \+ )?(\w+) \+ (0x[0-9a-f]+)\]|\[(\w+) \+ (0x[0-9a-f]+)\]')
rx=re.compile(r'\+ (0x[0-9a-f]+)\]')
for i in md.disasm(t,0x401000):
    if '[' not in i.op_str or i.mnemonic in('.byte',): continue
    for m in rx.finditer(i.op_str):
        d=int(m.group(1),16)
        if lo<=d<=hi: print(f'{i.address:08x} {i.mnemonic} {i.op_str}'); break
