"""Confronto parola per parola di un DTP Xbox grezzo contro B83: classe della conversione applicata e lettura f32/u16.
Uso: dtpcmp.py <file.drm> <id> [solo_sospetti]"""
import sys, os, struct
H = os.path.dirname(os.path.abspath(__file__)); T = os.path.join(H, '..', '..', '..', 'tools'); sys.path.insert(0, T)
import drm, drm_reloc as R
from wave_swap import raw_dlc
n, sid = sys.argv[1], int(sys.argv[2]); only = len(sys.argv) > 3
def sec(raw, e): return [x for x in drm.sections_with_data(drm.cdrm_decode(raw, e), e)[1] if x['type'] == 7 and x['id'] == sid][0]
x = sec(raw_dlc(n)[0], 'be'); p = sec(open(os.path.join(T, '..', 'work', 'baseline', 'B83', 'mods', n), 'rb').read(), 'le')
xr = R.parse(x['reloc'], 'be'); it = dict(xr.internal); ids = xr.id_offsets()
xd, pd = x['data'], p['data']; print('len', len(xd), len(pd))
for o in range(0, min(len(xd), len(pd)) - 3, 4):
    a, b = xd[o:o + 4], pd[o:o + 4]
    c = 's32' if a[::-1] == b else ('raw' if a == b else ('s16' if a[1::-1] + a[3:1:-1] == b else '??'))
    if a == b and a[::-1] == b: c = 'any'
    f = struct.unpack('>f', a)[0]; h = struct.unpack('>HH', a)
    tag = 'PTR' if o in it else ('ID%d' % ids[o] if o in ids else '')
    plaus_f = a != b'\0\0\0\0' and 1e-6 < abs(f) < 1e7
    sus = (c == 's32' and not plaus_f and not tag and h[0] not in (0, 0xffff) and h[1] != 0 and a[0] != 0) or c in ('??',)
    if only and not sus: continue
    print('%5x %-4s xb %s pc %s  f %-12.6g u16 %-14s %s %s' % (o, c, a.hex(), b.hex(), f, h, tag, '<<' if sus else ''))
