import sys, struct, bisect, collections, re
sys.path.insert(0, '/path/to/trudlcport/work/ws/codefirst/xbox_map')
from mapsym import *
LO, HI = 0x820e0000, 0x82765150
funcs = sorted(a for a, ns in by_addr.items() if LO <= a < HI)
def owner(a):
    i = bisect.bisect_right(funcs, a) - 1
    return funcs[i] if i >= 0 else None
SLOT = int(sys.argv[1], 0) if len(sys.argv) > 1 else 0x20
pat = re.compile(sys.argv[2] if len(sys.argv) > 2 else r'Light|Shadow|View|Scene')
data = img[LO - BASE:HI - BASE]; W = struct.unpack('>%dI' % (len(data) // 4), data)
hits = collections.defaultdict(list)
for i, w in enumerate(W):
    if (w & 0xFC00FFFF) == (0x80000000 | SLOT):
        rd = (w >> 21) & 31
        for j in range(i + 1, min(i + 5, len(W) - 1)):
            if W[j] == (0x7C0903A6 | (rd << 21)) and any(W[k] == 0x4E800421 for k in range(j + 1, min(j + 3, len(W)))):
                a = LO + 4 * i; hits[owner(a)].append(a); break
print('chiamate virtuali slot 0x%x: %d in %d funzioni' % (SLOT, sum(len(v) for v in hits.values()), len(hits)))
for f, v in sorted(hits.items()):
    n = nm(f) or '?'
    if pat.search(n): print('  %08x %s  siti: %s' % (f, n[:110], ' '.join('%x' % a for a in v)))
