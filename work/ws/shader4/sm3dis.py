"""sm3dis.py - disassemblatore D3D9 SM2/SM3 (bytecode -> testo). Il testo e' rimontabile con sm3asm.assemble().
uso: tools/venv/bin/python -I sm3dis.py file.bin     |  API: disassemble(bytes)->str, bytecode_len(bytes)->int"""
import struct, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sm3asm

def bytecode_len(b):
    """Lunghezza in byte fino al token FFFF incluso (commenti saltati)."""
    n = len(b) // 4
    t = struct.unpack_from('<%dI' % n, b, 0)
    i = 1
    while i < n:
        tok = t[i]; op = tok & 0xFFFF
        if op == 0xFFFF: return (i + 1) * 4
        if op == 0xFFFE: i += 1 + ((tok >> 16) & 0x7FFF); continue
        i += 1 + ((tok >> 24) & 0xF)
    raise ValueError('token di fine assente')

def disassemble(b, comments=True):
    return sm3asm.format_program(sm3asm.decode(b), comments)

def ctab_of(b):
    """Estrae [(name, regset, regidx, regcount)] dal commento CTAB (se c'e')."""
    p = sm3asm.decode(b)
    for it in p.items:
        if isinstance(it, sm3asm.Comment) and it.payload[:4] == b'CTAB':
            d = it.payload[4:]
            size, creator, version, n, cinfo, flags, target = struct.unpack_from('<7I', d, 0)
            out = []
            for k in range(n):
                no, rs, ri, rc, _r, ti, dv = struct.unpack_from('<IHHHHII', d, cinfo + 20 * k)
                e = d.find(b'\0', no)
                out.append((d[no:e].decode('latin1'), rs, ri, rc))
            return out
    return []

if __name__ == '__main__':
    b = open(sys.argv[1], 'rb').read()
    print(disassemble(b[:bytecode_len(b)]))
