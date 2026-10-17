"""Giro 6 task 4: cutscene DLC (cinstream/pdlc1_010_intro, pdlc1_030_finale): per ogni DTP-lista-comandi, il PC (mods) deve coincidere con cine_cmd.convert(Xbox)
(parole non id/non puntatore), e le sezioni devono avere lo stesso insieme (tipo,id) dell'Xbox. Poi il .mul: dimensione/intestazione vs Xbox.
Uso: cine_check.py MODS_DIR"""
import sys, os, struct, collections
ROOT = '/path/to/trudlcport'; sys.path.insert(0, ROOT + '/tools'); sys.path.insert(0, ROOT + '/work/ws/cine')
import drm, drm_reloc as R, cine_cmd as CC
from wave_swap import raw_dlc
mods = sys.argv[1].rstrip('/') + '/'
for name in ('cinstream/pdlc1_010_intro.drm', 'cinstream/pdlc1_030_finale.drm'):
    xr, _ = raw_dlc(name.replace('/', '\\'))
    X = drm.sections_with_data(drm.cdrm_decode(xr, 'be'), 'be')[1]
    P = drm.sections_with_data(drm.cdrm_decode(open(mods + name, 'rb').read(), 'le'), 'le')[1]
    xs = collections.Counter((s['type']) for s in X); ps = collections.Counter((s['type']) for s in P)
    print('==', name, 'sezioni Xbox', len(X), 'PC', len(P), 'tipi uguali' if xs == ps else 'TIPI DIVERSI %s %s' % (dict(xs), dict(ps)))
    pm = {(s['type'], s['id']): s for s in P}
    nd = nb = nw = 0; unk = []
    for x in X:
        if x['type'] != 7: continue
        p = pm.get((7, x['id']))
        if p is None: unk.append(('manca', x['id'])); continue
        d = x['data']
        if CC.fmt_of(d) is None or len(d) != len(p['data']): continue
        r = R.parse(x['reloc'], 'be')
        try: o, cl = CC.convert(d, None, {a for a, _ in r.internal})
        except ValueError: unk.append(('struttura', x['id'])); continue
        nd += 1; bad = 0
        for k in range(0, len(d) - 3, 4):
            if cl.get(k) in ('id', 'ptr') or k in {a for a, _ in r.internal}: continue
            nw += 1
            if o[k:k + 4] != p['data'][k:k + 4]: bad += 1
        nb += bad
        if bad: unk.append(('parole diverse', x['id'], bad))
    print('   DTP-lista-comandi validate', nd, 'parole controllate', nw, 'diverse', nb, '; anomalie', unk[:8])
    mul = name[:-4] + '.mul'
    mp = mods + mul
    print('   .mul PC', os.path.getsize(mp) if os.path.exists(mp) else 'ASSENTE', 'byte, intestazione', open(mp, 'rb').read(16).hex() if os.path.exists(mp) else '')
