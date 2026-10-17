"""Scansione overlay: DTP famiglia sezioni/effetti (header {id,0,ptr,{n,0},ptr->n x 0x17c}) vs regole imparate (fxdtp)."""
import sys, os, collections, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fxdtp as F, fx_apply as FA, cinepairs
sys.path.insert(0, cinepairs.T)
import drm
from wave_swap import raw_dlc
mods = sys.argv[1]; tab = F.learn(F.samples()); rows = []; tot = collections.Counter()
for f in sorted(os.listdir(mods)) + ['cinstream/' + x for x in sorted(os.listdir(os.path.join(mods, 'cinstream'))) if x.endswith('.drm')]:
    if not f.endswith('.drm'): continue
    xr, _ = raw_dlc(os.path.basename(f)) if '/' not in f else (None, None)
    if xr is None: continue
    X = [s for s in drm.sections_with_data(drm.cdrm_decode(xr, 'be'), 'be')[1] if s['type'] == 7]
    P = [s for s in drm.sections_with_data(drm.cdrm_decode(open(os.path.join(mods, f), 'rb').read(), 'le'), 'le')[1] if s['type'] == 7]
    if len(X) != len(P): continue
    for x, p in zip(X, P):
        if not F.is_fx(x['data']) or len(x['data']) != len(p['data']): continue
        try: new, st, unk = FA.conv_dtp(x['data'], x['reloc'], p['data'], lambda v: FA.TM.get(v), tab)
        except ValueError as e: tot['ko'] += 1; rows.append((f, x['id'], 'KO ' + str(e)[:50])); continue
        nd = [k for k in range(0, len(new) - 3, 4) if new[k:k + 4] != p['data'][k:k + 4]]
        tot['dtp'] += 1; tot['parole_diverse'] += len(nd); tot['dtp_diversi'] += bool(nd)
        if nd: rows.append((f, x['id'], p['id'], len(nd), len(new) // 4, st.get('ignota (tenuta B44)', 0)))
print(dict(tot))
for r in rows: print('  ', r)
