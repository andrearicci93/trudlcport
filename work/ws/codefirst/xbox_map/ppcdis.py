import sys; sys.path.insert(0, '/path/to/trudlcport/work/ws/codefirst/xbox_map')
from mapsym import *
from capstone import *
md = Cs(CS_ARCH_PPC, CS_MODE_32 | CS_MODE_BIG_ENDIAN); md.detail = False
def size_of(va):
    nxt = sorted(a for a in by_addr if a > va and 0x82110000 <= a)
    return (nxt[0] - va) if nxt else 0x100
def dis(va, n=None):
    n = n or min(size_of(va), 0x600)
    for i in md.disasm(img[va - BASE:va - BASE + n], va):
        print('%08x  %-8s %s' % (i.address, i.mnemonic, i.op_str))
if __name__ == '__main__':
    q = sys.argv[1]
    va = by_name[q] if q in by_name else int(q, 16)
    print(';', nm(va), hex(va)); dis(va, int(sys.argv[2], 0) if len(sys.argv) > 2 else None)
