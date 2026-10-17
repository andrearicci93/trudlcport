"""Scansione overlay: DTP famiglia comandi / effetti in tutti i DRM DLC; parole che i convertitori validati cambierebbero."""
import sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cinepairs, cine_cmd as CC, fxdtp as F, fx_apply as FA
sys.path.insert(0, cinepairs.T)
import drm, drm_reloc as R
from wave_swap import raw_dlc
mods = sys.argv[1]; tab = F.learn(F.samples())
tot = collections.Counter(); rows = []
for f in sorted(os.listdir(mods)):
    if not f.endswith('.drm'): continue
    xr, _ = raw_dlc(f)
    if xr is None: continue
    X = [s for s in drm.sections_with_data(drm.cdrm_decode(xr, 'be'), 'be')[1] if s['type'] == 7]
    P = [s for s in drm.sections_with_data(drm.cdrm_decode(open(os.path.join(mods, f), 'rb').read(), 'le'), 'le')[1] if s['type'] == 7]
    if len(X) != len(P): rows.append((f, 'numero DTP diverso')); continue
    for x, p in zip(X, P):
        xd = x['data']
        if len(xd) != len(p['data']): continue
        kind = 'cmd' if CC.fmt_of(xd) else 'fx' if F.is_fx(xd) else None
        if not kind: continue
        r = R.parse(x['reloc'], 'be'); keep = {a for a, _ in r.internal} | {o for _, o in r.idref}
        try:
            if kind == 'cmd': new, _ = CC.convert(xd, None, {a for a, _ in r.internal})
            else: new, st, unk = FA.conv_dtp(xd, x['reloc'], p['data'], lambda v: FA.TM.get(v, v), tab)
        except ValueError as e:
            tot[kind + '_struttura_ko'] += 1; rows.append((f, x['id'], kind, 'KO ' + str(e)[:60])); continue
        nd = sum(new[k:k + 4] != p['data'][k:k + 4] for k in range(0, len(new) - 3, 4) if k not in keep)
        tot[kind] += 1; tot[kind + '_parole_diverse'] += nd; tot[kind + '_dtp_da_correggere'] += nd > 0
        if nd: rows.append((f, x['id'], p['id'], kind, nd, len(new) // 4))
print(dict(tot))
for r in rows: print('  ', r)
