"""Record di collegamento fra giunti UberObject (byte0 = 0x0b, +4/+8 puntatori interni a due record giunto diversi):
il campo +0xc e' un float (rapporto, letto con fld da FUN_004d7ed0 0x4d7f31; base: 23/23 convertiti s32).
Elenca i DTP DLC dove la baseline NON ha +0xc = s32(Xbox). Uso: link_scan.py [baseline=B83]"""
import sys, os, struct
H = os.path.dirname(os.path.abspath(__file__)); T = os.path.join(H, '..', '..', '..', 'tools'); sys.path.insert(0, T)
import drm, drm_reloc as R
from wave_swap import raw_dlc
B = sys.argv[1] if len(sys.argv) > 1 else 'B83'
M = os.path.join(T, '..', 'work', 'baseline', B, 'mods')
bad = ok = 0
for n in sorted(f for f in os.listdir(M) if f.endswith('.drm')):
    xr, _ = raw_dlc(n)
    if xr is None: continue
    X = {(s['type'], s['id']): s for s in drm.sections_with_data(drm.cdrm_decode(xr, 'be'), 'be')[1] if s['type'] == 7}
    P = {(s['type'], s['id']): s for s in drm.sections_with_data(drm.cdrm_decode(open(os.path.join(M, n), 'rb').read(), 'le'), 'le')[1] if s['type'] == 7}
    for k, x in X.items():
        p = P.get(k)
        if p is None or len(p['data']) != len(x['data']): continue
        xd, pd = x['data'], p['data']; it = dict(R.parse(x['reloc'], 'be').internal)
        for o in range(0, len(xd) - 0x10, 4):
            if xd[o] == 0x0b and xd[o + 1:o + 4] == b'\0\0\0' and (o + 4) in it and (o + 8) in it and it[o + 4] != it[o + 8] \
               and xd[it[o + 4]] in (0, 1, 2, 3, 4) and xd[it[o + 8]] in (0, 1, 2, 3, 4):
                a, b = xd[o + 12:o + 16], pd[o + 12:o + 16]
                if a[::-1] == b: ok += 1; continue
                bad += 1
                print('%s DTP %d @%d  xb %s (%.4g)  %s %s' % (n, k[1], o, a.hex(), struct.unpack('>f', a)[0], B, b.hex()))
print('collegamenti corretti', ok, 'sbagliati', bad)
