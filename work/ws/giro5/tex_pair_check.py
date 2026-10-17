"""Confronto texel reali Xbox vs PC per TUTTI i sampler dei materiali di un DRM (coppie xbox_tex/pc_tex): media RGBA per canale, cubi sulle 6 facce.
DXN: Xbox (x,y) contro PC (R=x, A=y). Segnala differenze > soglia (canale scambiato, tinta, alfa)."""
import sys, io, contextlib, struct
import numpy as np
sys.path.insert(0, '/path/to/trudlcport/work/ws/giro5')
with contextlib.redirect_stdout(io.StringIO()):
    import build_unlit as B
import texlib
BASELINE = sys.argv[1] if len(sys.argv) > 1 else 'B87_materiali19'
DRM = sys.argv[2] if len(sys.argv) > 2 else 'dlc_caverns_hall.drm'
texlib.set_baseline(BASELINE)
F14 = B.F14; C = F14.C; L = B.libs(); DM = L['DM']
tree = C.read_tree(B.ROOT + '/work/baseline/%s/mods' % BASELINE)
secs = {(s.type, s.id): s for s in tree[DRM].sections}
seen = {}; tot = 0; nocov = 0
for (t, mid), ms in sorted(secs.items()):
    if t != 10 or mid not in DM: continue
    dl = struct.unpack_from('>4I', DM[mid][0], 0x28)[2]
    try: _, rows = F14.derive_slotmap(mid, dl, ms.data, ms.reloc)
    except Exception as ex: print('mat', mid, 'derive fallito', ex); continue
    for r in rows:
        if r['type'] == 0 and r['flag'] in (9, 10): continue
        tot += 1
        key = (r['xbox_tex'], r['pc_tex'])
        if key in seen: seen[key].append(mid); continue
        seen[key] = [mid]
bad = []
for (xt, pt), mids in sorted(seen.items()):
    x = texlib.xb_mean(xt); p = texlib.pc_mean(pt)
    if x is None or p is None or x['rgba'] is None or p['rgba'] is None: nocov += 1; print('NON DECODIFICATA', xt, pt, None if x is None else x['kind'], None if p is None else p['kind'], mids[:3]); continue
    xr, pr = x['rgba'], p['rgba']
    if x['kind'] == 'DXN': d = np.array([pr[0] - xr[0], 0, 0, pr[3] - xr[1]])
    else: d = pr - xr
    if x['kind'] in ('DXT1',): d[3] = 0
    flag = np.abs(d).max() > 0.03
    if flag: bad.append((np.abs(d).max(), xt, pt, x['kind'], p['kind'], x['cube'], np.round(xr, 3), np.round(pr, 3), mids[:3]))
print('sampler totali %d, coppie uniche %d, non decodificate %d, DIFFERENTI(>0.03) %d' % (tot, len(seen), nocov, len(bad)))
for b in sorted(bad, key=lambda b: -b[0]): print(b)
