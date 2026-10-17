"""Tiny x86 helper for the menu_dlc investigation (tru_steam.exe.unpacked.exe: file offset == VA - 0x400000).
Usage: tools/venv/bin/python -I tools/menu_dlc_x86.py dis VA [N]       disassemble N instructions
       tools/venv/bin/python -I tools/menu_dlc_x86.py str VA             C string at VA
       tools/venv/bin/python -I tools/menu_dlc_x86.py refs VA            code/data words equal to VA
"""
import sys, struct, re
import capstone
EXE = '/path/to/trudlcport/work/laa/tru_steam.exe.unpacked.exe'
B = open(EXE, 'rb').read()
BASE = 0x400000
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)

def cstr(va):
    o = va - BASE; z = B.find(b'\0', o)
    return B[o:z].decode('latin1')

def dis(va, n=40):
    out = []
    for i, ins in enumerate(md.disasm(B[va - BASE:va - BASE + n * 16], va)):
        if i >= n: break
        ann = ''
        for m in re.finditer(r'0x([0-9a-f]{6,8})', ins.op_str):
            v = int(m.group(1), 16)
            if 0x83e000 <= v < 0x88e000:
                s = cstr(v)
                if len(s) >= 3 and all(32 <= ord(c) < 127 for c in s): ann = ' ; %r' % s[:60]
        out.append('%08x  %-8s %s%s' % (ins.address, ins.mnemonic, ins.op_str, ann))
    return out

def refs(va):
    pat = struct.pack('<I', va)
    return [m.start() + BASE for m in re.finditer(re.escape(pat), B)]

if __name__ == '__main__':
    c = sys.argv[1]; v = int(sys.argv[2], 16)
    if c == 'dis': print('\n'.join(dis(v, int(sys.argv[3]) if len(sys.argv) > 3 else 40)))
    elif c == 'str': print(repr(cstr(v)))
    elif c == 'refs': print([hex(x) for x in refs(v)])
