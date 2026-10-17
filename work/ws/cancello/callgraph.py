"""Per ogni funzione di uno script (B83): nome prototipo, vtIndex, range di codice, e i riferimenti nel codice
(EXT verso altri script/offset, ID8, puntatori a stringhe). Uso: callgraph.py <file.drm> <id script>"""
import sys, os, struct, re
H = os.path.dirname(os.path.abspath(__file__)); T = os.path.join(H, '..', '..', '..', 'tools'); sys.path.insert(0, T)
import drm, drm_reloc as R, script_conv as SC
name, sid = sys.argv[1], int(sys.argv[2])
secs = drm.sections_with_data(drm.cdrm_decode(open(os.path.join(T, '..', 'work', 'baseline', 'B83', 'mods', name), 'rb').read(), 'le'), 'le')[1]
s = [x for x in secs if x['type'] == 8 and x['id'] == sid][0]; d = s['data']; r = R.parse(s['reloc'], 'le'); it = dict(r.internal)
ext = {so: (secs[si]['id'], do) for si, so, do in r.external}; ids = r.id_offsets()
W = SC.walk(d, r, 'le')
def cstr(o):
    e = d.find(b'\0', o); t = d[o:e]
    return t.decode('latin1') if t and all(32 <= c < 127 for c in t) else None
codes = []
for nm, t, n, sz in W.arrays:
    if nm != 'funcs': continue
    for k in range(n):
        a = t + k * sz; pp = it.get(a); c = it.get(a + 0x18)
        pn = struct.unpack_from('<H', d, pp + 8)[0] if pp is not None else None
        vt = struct.unpack_from('<H', d, pp + 6)[0] if pp is not None else None
        if c is not None: codes.append((c, k, pn, vt, d[a + 5]))
codes.sort()
for i, (c, k, pn, vt, st) in enumerate(codes):
    n = struct.unpack_from('<I', d, c - 4)[0]; end = c + 4 * n
    refs = []
    for o in range(c, end, 4):
        if o in ext: refs.append('EXT%d+%d' % ext[o])
        elif o in ids: refs.append('ID%d:%d' % (ids[o], struct.unpack_from('<I', d, o)[0]))
        elif o in it:
            sv = cstr(it[o]); refs.append(repr(sv) if sv else 'ptr+%x' % it[o])
    print('func %d nome %s vt %s stato %s codice %x..%x' % (k, pn, vt, st, c, end))
    print('   ', ' '.join(refs))
