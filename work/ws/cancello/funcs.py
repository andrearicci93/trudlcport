"""Funzioni di uno script: indirizzo, prototipo (nome simbolo, flags/callType/vtIndex), stato, inizio del codice.
Uso: funcs.py <file.drm> <id script> [pc|xb]"""
import sys, os, struct
H = os.path.dirname(os.path.abspath(__file__)); T = os.path.join(H, '..', '..', '..', 'tools'); sys.path.insert(0, T)
import drm, drm_reloc as R, script_conv as SC
from wave_swap import raw_dlc
name, sid = sys.argv[1], int(sys.argv[2]); side = sys.argv[3] if len(sys.argv) > 3 else 'pc'
raw, e = (open(os.path.join(T, '..', 'work', 'baseline', 'B83', 'mods', name), 'rb').read(), 'le') if side == 'pc' else (raw_dlc(name)[0], 'be')
E = '<' if e == 'le' else '>'
secs = drm.sections_with_data(drm.cdrm_decode(raw, e), e)[1]
s = [x for x in secs if x['type'] == 8 and x['id'] == sid][0]; d = s['data']; r = R.parse(s['reloc'], e); it = dict(r.internal)
ext = {so: (secs[si]['id'], do) for si, so, do in r.external}
W = SC.walk(d, r, e)
for nm, t, n, sz in W.arrays:
    if nm in ('states', 'funcs', 'protos', 'sfi'): print('array', nm, 'a', hex(t), 'n', n, 'sz', sz)
for nm, t, n, sz in W.arrays:
    if nm != 'funcs': continue
    for k in range(n):
        a = t + k * sz
        pp = it.get(a); pe = ext.get(a)
        proto = ('int', pp) if pp is not None else ('ext', pe)
        pname = struct.unpack_from(E + 'H', d, pp + 8)[0] if pp is not None else None
        pfl = d[pp + 4:pp + 8].hex() if pp is not None else None
        flags, state = d[a + 4], d[a + 5]
        code = it.get(a + 0x18)
        print('func', k, '@', hex(a), 'proto', proto, 'nome', pname, 'proto+4', pfl, 'flags', flags, 'stato', state, 'codice', code and hex(code))
