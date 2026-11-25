"""introdata_cmp.py - (20/11/2026) solo lettura. Per le intro di una unit (record 0x90) segue i puntatori interni che partono
dal record (rilocazioni con sorgente nel record) e confronta i blocchi puntati Xbox/PC parola per parola (classe s32/raw/s16/altro,
slot di rilocazione esclusi). Stampa per oggetto i conteggi e le parole non s32. uso: introdata_cmp.py BASELINE UNIT.drm [oggetto_regex]"""
import sys, struct, re, bisect, collections
sys.path.insert(0, '/path/to/trudlcport/work/ws/lukas_check/inv'); sys.path.insert(0, '/path/to/trudlcport/tools')
import inv_common as C, drm_write as DW, drm_reloc as R
BL, U = sys.argv[1:3]; rx = re.compile(sys.argv[3] if len(sys.argv) > 3 else '.')
names = {}
for l in open('/path/to/trudlcport/work/baseline/%s/mods/tr8/pc-w/objectlist.txt' % BL, errors='ignore'):
    p = l.split(',', 1)
    if len(p) == 2 and p[0].strip().isdigit(): names[int(p[0])] = p[1].strip()
def unit(D, e):
    for si, so, do in R.parse(bytes(D.sections[0].reloc), e).external:
        if so == 0x74: return D.sections[si]
P = unit(DW.read(open('/path/to/trudlcport/work/baseline/%s/mods/%s' % (BL, U), 'rb').read(), 'le'), 'le'); X = unit(DW.read(C.xbox(U), 'be'), 'be')
assert len(P.data) == len(X.data)
rp, rx_ = R.parse(bytes(P.reloc), 'le'), R.parse(bytes(X.reloc), 'be')
ip, ix = dict(rp.internal), dict(rx_.internal)
sl = {o for o, _ in rp.internal} | {o for _, o in list(rp.idref) + list(rp.idref_a)} | {o for o, _ in rx_.internal} | {o for _, o in list(rx_.idref) + list(rx_.idref_a)}
T = sorted(set(ip.values()) | {0, len(P.data)})
def blk(t): i = bisect.bisect_right(T, t); return t, T[i] if i < len(T) else len(P.data)
n = struct.unpack_from('<I', P.data, 0xc)[0]; A = ip[0x10]
def cls(x, p):
    if x == p: return 'pal' if x == x[::-1] else 'raw'
    if p == x[::-1]: return 's32'
    if p == x[1::-1] + x[:1:-1]: return 's16'
    return 'altro'
agg = collections.defaultdict(collections.Counter)
for k in range(n):
    r = A + 0x90 * k; oid = struct.unpack_from('<H', P.data, r + 0x50)[0]; nm = names.get(oid, '?'); uid = struct.unpack_from('<I', P.data, r + 0x58)[0]
    if not rx.search(nm): continue
    for s in range(r, r + 0x90, 4):
        if s not in ip: continue
        t0, t1 = blk(ip[s]); assert ix.get(s) == ip[s], (k, hex(s))
        bad = []
        for o in range(t0, t1 - 3, 4):
            if o in sl: continue
            c = cls(bytes(X.data[o:o + 4]), bytes(P.data[o:o + 4])); agg[nm][c] += 1
            if c not in ('s32', 'pal'): bad.append('+%#x %s->%s %s' % (o - t0, X.data[o:o + 4].hex(), P.data[o:o + 4].hex(), c))
        print('%-32s uid %6d rec+%#x -> blocco %#x (%d B): %s' % (nm, uid, s - r, t0, t1 - t0, '; '.join(bad[:16]) or 'tutto s32'))
print('--- per oggetto')
for nm, c in sorted(agg.items()): print('%-36s %s' % (nm, dict(c)))
