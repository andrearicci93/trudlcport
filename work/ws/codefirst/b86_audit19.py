"""Stato dei 19 materiali nell'albero B86_contratti: DRM che li contengono, pos2 PC, surrogato originale, uguaglianza delle copie, presenza della lib."""
import sys, os, struct, collections; S4='/path/to/trudlcport/work/ws/shader4'; sys.path.insert(0, S4); sys.path.insert(0, '/path/to/trudlcport/work/ws/codefirst')
import f12_build_all as F12
from f12_build_all import *
FAM19 = {20344, 21093, 21258, 22596, 22597, 23186, 23437, 24043, 21086, 21209, 23371, 23372, 21087, 23568, 20992, 23375, 20856, 20857, 21126}
B86 = '/path/to/trudlcport/work/baseline/B86_contratti/mods'
L = libs(); DM = L['DM']
lit = {int(r['id_xbox']) for r in __import__('csv').DictReader(open(S4 + '/illuminati.tsv'), delimiter='\t')}
for label, src in (('B73', F12.SRC), ('B86', B86)):
    occ, secs = material_occurrences(src, DM, lambda dl: dl in lit)
    print('===', label, src)
    bad = 0
    for mid in sorted(FAM19):
        items = occ.get(mid, [])
        if not items: print('  mat %d: ASSENTE' % mid); bad += 1; continue
        dl = struct.unpack_from('>4I', DM[mid][0], 0x28)[2]
        why = shared_problem(dl, items, secs)
        pcs = sorted({struct.unpack_from('<I', x.data, 0x30)[0] for _, x in items})
        print('  mat %5d dl %d | %d DRM | pos2 %s (orig %s) | copie %d distinte | %s' % (mid, dl, len(items), pcs, original_surrogate(dl), len({s.data for _, s in items}), why or 'OK'))
        bad += bool(why)
    print('  problemi:', bad)
