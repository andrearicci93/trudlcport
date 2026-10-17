import re, struct, collections
MAP = '/path/to/Recomp/[X360] Tomb Raider Underworld [2007-08-18] (MAP)/tr8_Content.map'
IMG = '/path/to/trudlcport/work/ws/codefirst/xbox_map/tr8_Content.bin'
BASE = 0x82000000
rx = re.compile(r'^\s*([0-9a-f]{4}):([0-9a-f]{8})\s+(\S+)\s+([0-9a-f]{8})\s')
by_addr = collections.defaultdict(list); by_name = {}
for ln in open(MAP, errors='replace'):
    m = rx.match(ln)
    if m:
        va = int(m.group(4), 16); by_addr[va].append(m.group(3)); by_name[m.group(3)] = va
img = open(IMG, 'rb').read()
def u32(va): o = va - BASE; return struct.unpack('>I', img[o:o + 4])[0]
def nm(va): return by_addr.get(va, ['?'])[0] if va in by_addr else None
def vtable(name, n=40):
    va = by_name[name]; out = []
    for i in range(n):
        p = u32(va + 4 * i)
        if not (0x82000000 <= p < 0x83220000): break
        out.append((i, 4 * i, p, nm(p)))
    return va, out
if __name__ == '__main__':
    import sys
    for q in sys.argv[1:]:
        cands = [k for k in by_name if q in k]
        for k in cands[:6]:
            va, v = vtable(k)
            print('==', k, hex(va))
            for i, off, p, n in v: print('  [%2d] +0x%02x %08x %s' % (i, off, p, n))
