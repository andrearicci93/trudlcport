"""Cerca un id oggetto (u16) nelle sezioni script (tipo 8) di tutti i DRM della B83 e dei rispettivi Xbox grezzi.
Uso: find_objref.py <id oggetto>"""
import sys, os, struct
H = os.path.dirname(os.path.abspath(__file__)); T = os.path.join(H, '..', '..', '..', 'tools'); sys.path.insert(0, T)
import drm, drm_reloc as R, script_conv as SC
from wave_swap import raw_dlc
oid = int(sys.argv[1]); M = os.path.join(T, '..', 'work', 'baseline', 'B83', 'mods')
for n in sorted(f for f in os.listdir(M) if f.endswith('.drm')):
    xr, _ = raw_dlc(n)
    for side, raw, e in (('xb', xr, 'be'), ('pc', open(os.path.join(M, n), 'rb').read(), 'le')):
        if raw is None: continue
        E = '>' if e == 'be' else '<'
        for s in drm.sections_with_data(drm.cdrm_decode(raw, e), e)[1]:
            if s['type'] != 8 or not s['data']: continue
            d = s['data']; lab = None
            for o in range(0, len(d) - 1, 2):
                if struct.unpack_from(E + 'H', d, o)[0] == oid:
                    if lab is None:
                        try: lab = SC.walk(d, R.parse(s['reloc'], e), e).lab
                        except Exception: lab = {}
                    print(side, n, 'script', s['id'], 'off', hex(o), d[o & ~3:(o & ~3) + 8].hex(), lab.get(o & ~3))
