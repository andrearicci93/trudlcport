import sys, struct
from capstone import *
class Img:
    def __init__(s, path):
        d = open(path, 'rb').read(); s.d = d
        pe = struct.unpack_from('<I', d, 0x3c)[0]
        nsec = struct.unpack_from('<H', d, pe + 6)[0]; osz = struct.unpack_from('<H', d, pe + 20)[0]
        s.base = struct.unpack_from('<I', d, pe + 24 + 28)[0]
        s.secs = []
        so = pe + 24 + osz
        for i in range(nsec):
            n, vs, va, rs, rp = struct.unpack_from('<8sIIII', d, so + 40 * i)
            s.secs.append((va, vs, rp, rs))
    def read(s, va, n):
        rva = va - s.base
        for v, vs, rp, rs in s.secs:
            if v <= rva < v + max(vs, rs):
                o = rp + rva - v
                return s.d[o:o + n]
        raise ValueError(hex(va))
def dis(img, va, n=200):
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    for i in md.disasm(img.read(va, n * 8), va):
        print('%x: %s %s' % (i.address, i.mnemonic, i.op_str))
        n -= 1
        if n <= 0: break
if __name__ == '__main__':
    dis(Img(sys.argv[1]), int(sys.argv[2], 16), int(sys.argv[3]))
