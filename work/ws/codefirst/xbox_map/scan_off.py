import sys, struct, bisect, collections
sys.path.insert(0, '/path/to/trudlcport/work/ws/codefirst/xbox_map')
from mapsym import *
LO, HI = 0x820e0000, 0x82765150
funcs = sorted(a for a, ns in by_addr.items() if LO <= a < HI)
def owner(a):
    i = bisect.bisect_right(funcs, a) - 1; return funcs[i]
off = int(sys.argv[1], 0)
data = img[LO - BASE:HI - BASE]; W = struct.unpack('>%dI' % (len(data) // 4), data)
kinds = {'stw': 0x90000000, 'lwz': 0x80000000, 'stb': 0x98000000, 'lbz': 0x88000000}
for k, base in kinds.items():
    for i, w in enumerate(W):
        if (w & 0xFC00FFFF) == (base | off):
            a = LO + 4 * i; f = owner(a)
            print('%s %08x in %08x %s' % (k, a, f, (nm(f) or '?')[:100]))
