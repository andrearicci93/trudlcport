"""model58_cmp.py - (20/11/2026) solo lettura. Modelli (DTP 0x04c20453): tabella header +0x54 n / +0x58 -> record da 0x5c B.
Nel base (store.pkl) conta per offset di record la classe PC della parola Xbox (s32/s16/raw/b2s16/s16b2, 'pal' escluso), poi
confronta i record del modello DLC indicato. uso: model58_cmp.py BASELINE FILE.drm DTP"""
import sys, pickle, json, struct, collections
sys.path.insert(0, '/path/to/trudlcport/work/ws/lukas_check/inv'); sys.path.insert(0, '/path/to/trudlcport/tools')
import inv_common as C, drm_write as DW, drm_reloc as R
S = pickle.load(open('/path/to/trudlcport/work/generic/store.pkl', 'rb')); im = C.idmap().get(7, {})
MAG = bytes.fromhex('04c20453'); ST = 0x5c
def cls(a, b):
    if a == b: return 'pal' if a == a[::-1] else 'raw'
    if b == a[::-1]: return 's32'
    if b == a[1::-1] + a[:1:-1]: return 's16'
    if b == a[:2] + a[3:1:-1]: return 'b2s16'
    if b == a[1::-1] + a[2:]: return 's16b2'
    return 'altro'
base = collections.defaultdict(collections.Counter); nb = 0
for (t, x), xs in S['xb_store'].items():
    if t != 7 or xs['data'][:4] != MAG: continue
    p = S['pc_store'].get((7, im.get(x, x)))
    if not p or len(p['data']) != len(xs['data']): continue
    it = dict(R.parse(xs['reloc'], 'be').internal); T = it.get(0x58)
    if T is None: continue
    n = struct.unpack_from('>I', xs['data'], 0x54)[0]
    if not n or T + ST * n > len(xs['data']): continue
    sl = set(it) | {o for _, o in list(R.parse(xs['reloc'], 'be').idref) + list(R.parse(xs['reloc'], 'be').idref_a)}
    nb += 1
    for k in range(n):
        for o in range(0, ST, 4):
            a = T + ST * k + o
            if a in sl: continue
            c = cls(xs['data'][a:a + 4], p['data'][a:a + 4])
            if c != 'pal': base[o][c] += 1
print('modelli base con tabella +0x58:', nb)
for o in range(0, ST, 4): print('  +%#04x %s' % (o, dict(base[o])))
BL, F, D = sys.argv[1], sys.argv[2], int(sys.argv[3])
x = [s for s in DW.read(C.xbox(F), 'be').sections if s.type == 7 and s.id == D][0]
p = [s for s in DW.read(open('/path/to/trudlcport/work/baseline/%s/mods/%s' % (BL, F), 'rb').read(), 'le').sections if s.type == 7 and s.id == D][0]
it = dict(R.parse(bytes(x.reloc), 'be').internal); T = it[0x58]; n = struct.unpack_from('>I', x.data, 0x54)[0]
print('DLC', D, 'n', n, 'T', hex(T))
for k in range(n):
    for o in range(0, ST, 4):
        a = T + ST * k + o
        if a in it: continue
        c = cls(bytes(x.data[a:a + 4]), bytes(p.data[a:a + 4])); b = base[o]
        if c != 'pal' and b and b.most_common(1)[0][0] != c:
            print('  rec %d +%#04x xbox %s pc %s %s (base %s)' % (k, o, x.data[a:a + 4].hex(), p.data[a:a + 4].hex(), c, dict(b)))
