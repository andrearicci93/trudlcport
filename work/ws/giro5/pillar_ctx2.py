import sys, struct
sys.path.insert(0, '/path/to/trudlcport/tools'); sys.path.insert(0, '/path/to/trudlcport/work/ws/giro5')
import drm
from archive import Archive
from names import load, L
R = '/path/to/trudlcport/work/baseline/B87_materiali19/mods/'
C = '/path/to/Xenia-SteveRepack/Content/534307EC/00000002/'; xn = load(L + 'Tomb Raider Underworld (Xenon).txt')
for nm in ('dlc1_uo_pillar_of_doom_a.drm',):
    pcs = drm.sections_with_data(drm.cdrm_decode(open(R + nm, 'rb').read(), 'le'), 'le')[1]
    xbs = None
    for pk in [C + '9CA70CF0EDA43654D158C2E37470D301DFA850E753/pack10.000', C + '600A12643FCDAC84003E6E0DBD0A1A8F7DAE9DD153/pack11.000']:
        A = Archive(pk, 'be')
        for r in A.idx:
            if xn.get(r['hash'], '').split('\\')[-1] == nm: xbs = drm.sections_with_data(drm.cdrm_decode(A.read(r), 'be'), 'be')[1]
    print('Xbox sezioni con id 1039:', [(s['type'], s['id'], len(s['data'])) for s in xbs if s['id'] == 1039], '| id 1174:', [(s['type'], s['id']) for s in xbs if s['id'] == 1174])
    print('PC   sezioni con id 3634:', [(s['type'], s['id'], len(s['data'])) for s in pcs if s['id'] == 3634], '| id 1174:', [(s['type'], s['id']) for s in pcs if s['id'] == 1174])
    print('tipi presenti Xbox:', sorted({s['type'] for s in xbs}), 'PC:', sorted({s['type'] for s in pcs}))
    print('Xbox tipo 6 ids:', [s['id'] for s in xbs if s['type'] == 6][:20], 'PC tipo 6 ids:', [s['id'] for s in pcs if s['type'] == 6][:20])
    # chi altri nel DRM referenzia 1039 (Xbox) / 3634 / 1174 (PC) come u32
    for lab, secs, E, vals in (('Xbox', xbs, '>', (1039,)), ('PC', pcs, '<', (3634, 1174))):
        for s in secs:
            d = s['data']
            if s['type'] not in (0, 7, 8) or not d: continue
            for v in vals:
                pat = struct.pack(E + 'I', v); i = -1
                while True:
                    i = d.find(pat, i + 1)
                    if i < 0: break
                    if i % 4 == 0: print('  ', lab, 'ref u32', v, 'in tipo', s['type'], 'id', s['id'], 'off', hex(i))
