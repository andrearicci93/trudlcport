"""Parole float isolate convertite male: parola Xbox = float 'plausibile' (1e-3 <= |v| <= 1e5, non intero piccolo),
almeno 2 parole vicine (+-4/8) sono float plausibili convertiti s32 sul PC, e il PC NON ha lo swap s32 della parola.
Esclude slot reloc. uso: float_scan.py MODS [--exclude costume]"""
import sys, os, struct, math
T = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'); sys.path.insert(0, T)
import drm, drm_reloc as R
from wave_swap import raw_dlc
def plaus(b):
    v = struct.unpack('>f', b)[0]
    if not math.isfinite(v) or v == 0: return False
    a = abs(v); e = (struct.unpack('>I', b)[0] >> 23) & 0xff
    return 1e-3 <= a <= 1e5 and 100 <= e <= 160 and (struct.unpack('>I', b)[0] & 0xfff) != 0 or a in (0.5, 1.0, 2.0, 0.25)
mods = sys.argv[1]; rows = []
for dp, dn, fn in os.walk(mods):
    for f in fn:
        if not f.endswith('.drm') or 'costume' in f: continue
        rel = os.path.relpath(os.path.join(dp, f), mods)
        if '/' in rel: continue
        xr, _ = raw_dlc(f)
        if xr is None: continue
        X = [s for s in drm.sections_with_data(drm.cdrm_decode(xr, 'be'), 'be')[1] if s['type'] == 7]
        P = [s for s in drm.sections_with_data(drm.cdrm_decode(open(os.path.join(dp, f), 'rb').read(), 'le'), 'le')[1] if s['type'] == 7]
        if len(X) != len(P): continue
        for x, p in zip(X, P):
            xd, pd = x['data'], p['data']
            if len(xd) != len(pd): continue
            r = R.parse(x['reloc'], 'be'); sl = {a for a, _ in r.internal} | {o for _, o in r.idref}
            ok = lambda o: 0 <= o and o + 4 <= len(xd) and o not in sl and plaus(xd[o:o + 4]) and pd[o:o + 4] == xd[o:o + 4][::-1]
            for o in range(0, len(xd) - 3, 4):
                if o in sl or not plaus(xd[o:o + 4]) or pd[o:o + 4] == xd[o:o + 4][::-1]: continue
                nb = sum(ok(o + d) for d in (-8, -4, 4, 8))
                if nb >= 2: rows.append((f, x['id'], hex(o), xd[o:o + 4].hex(), pd[o:o + 4].hex(), round(struct.unpack('>f', xd[o:o + 4])[0], 3), nb))
for r in rows: print(r)
print('totale', len(rows))
