"""Giro 7 punto 3: MaterialParams di TUTTI i materiali di un DRM (default dlc_caverns_hall.drm) vs Xbox vergine.
Per materiale: lib Xbox / lib PC (+ tipo: 'nostra'>=2775, 'PC stock' se in P, 'surrogato' altrimenti), n. record Xbox/PC, record differenti con crominanza
(R-(G+B)/2) Xbox vs PC. Segnala 'TINTA+' quando un record PC e' piu' rosso del corrispondente Xbox (>0.02) con stesso layout.
Uso: hall_params_audit.py [MODS_DIR] [DRM...]"""
import sys, io, contextlib, struct, os
import numpy as np
sys.path.insert(0, '/path/to/trudlcport/work/ws/giro5')
with contextlib.redirect_stdout(io.StringIO()):
    import web_eval2 as W
F10, C, L = W.F10, W.C, W.L
D, DM, P = L['D'], L['DM'], L['P']
ROOT = '/path/to/trudlcport'
MODS = sys.argv[1] if len(sys.argv) > 1 else ROOT + '/work/baseline/B88b_acqua/mods'
DRMS = sys.argv[2:] or ['dlc_caverns_hall.drm']
tree = C.read_tree(MODS)
chroma = lambda v: float(v[0] - (v[1] + v[2]) / 2)
tot = {}
for rel in DRMS:
    secs = {(s.type, s.id): s for s in tree[rel].sections}
    print('#### %s: %d materiali' % (rel, sum(1 for k in secs if k[0] == 10)))
    for (t, mid), ms in sorted(secs.items()):
        if t != 10: continue
        if mid not in DM: print('mat %d: nessun Xbox vergine (solo PC)' % mid); continue
        dl = struct.unpack_from('>4I', DM[mid][0], 0x28)[2]; pcl = struct.unpack_from('<4I', ms.data, 0x28)[2]
        kind = 'nostra' if pcl >= 2775 else ('PC-stock' if pcl in P else 'surrogato(%s)' % ('lib nel DRM' if (9, pcl) in secs else 'lib fuori'))
        XPm = [np.array(v, np.float32) for v in F10.params(F10.f9_common._Sec(*DM[mid]), 'be')]; PPm = [np.array(v, np.float32) for v in F10.params(ms, 'le')]
        diffs = []
        if len(XPm) == len(PPm):
            for j, (a, b) in enumerate(zip(XPm, PPm)):
                if not np.allclose(a, b, atol=1e-6): diffs.append((j, a, b))
        tint = [(j, round(chroma(b) - chroma(a), 3)) for j, a, b in diffs if chroma(b) - chroma(a) > 0.02]
        orph = [(j, b) for j, b in enumerate(PPm) if not any(np.allclose(a, b, atol=1e-5) for a in XPm)]      # rec PC che non esistono fra i rec Xbox (qualunque posizione)
        orph = [(j, b) for j, b in orph if not (len(b) == 4 and False)]
        otint = [(j, round(chroma(b), 3)) for j, b in orph if chroma(b) > 0.05]
        key = (kind.split('(')[0], 'uguali' if len(XPm) == len(PPm) and not diffs else ('layout diverso' if len(XPm) != len(PPm) else 'differiscono'))
        tot[key] = tot.get(key, 0) + 1
        flag = (' TINTA+ rec %s' % tint if tint else '') + (' ORFANI(non in Xbox) %s' % [j for j, _ in orph] if orph else '') + (' ORFANI_ROSSI %s' % otint if otint else '')
        if diffs or len(XPm) != len(PPm) or orph:
            print('mat %d libX %d libPC %d [%s] rec X=%d PC=%d  differenti=%s%s' % (mid, dl, pcl, kind, len(XPm), len(PPm), [d[0] for d in diffs] if len(XPm) == len(PPm) else 'n/a', flag))
            for j, a, b in diffs[:6]: print('      rec %d X=%s PC=%s' % (j, np.round(a, 3), np.round(b, 3)))
        else: print('mat %d libX %d libPC %d [%s] params identici (%d rec)' % (mid, dl, pcl, kind, len(XPm)))
print('\nRIEPILOGO', tot)
