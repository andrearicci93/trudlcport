"""Giro 6 task 4: i float corretti in B47 (dungeon 20256 x59, dungeonhallb 20133 x7, pillar_of_doom_b 20478 x2, dungeon 20258 x1) sono presenti nel candidato?
Confronto per sezione DTP fra una baseline di riferimento e la dir MODS: parole diverse = float non portati. Uso: b47_floats.py REF_BASELINE MODS_DIR"""
import sys, os, struct
ROOT = '/path/to/trudlcport'; sys.path.insert(0, ROOT + '/tools')
import drm
ref = ROOT + '/work/baseline/%s/mods/' % sys.argv[1]; mods = sys.argv[2].rstrip('/') + '/'
for rel, tid in (('dlc_dungeon.drm', 20256), ('dlc_dungeonhallb.drm', 20133), ('dlc1_uo_pillar_of_doom_b.drm', 20478), ('dlc_dungeon.drm', 20258)):
    g = lambda base: {(s['type'], s['id']): s['data'] for s in drm.sections_with_data(drm.cdrm_decode(open(base + rel, 'rb').read(), 'le'), 'le')[1]}
    a = g(ref)[(7, tid)]; b = g(mods)[(7, tid)]
    diff = [o for o in range(0, min(len(a), len(b)), 4) if a[o:o + 4] != b[o:o + 4]]
    print('%-34s DTP %d  len %d/%d  parole diverse rispetto a %s: %d %s' % (rel, tid, len(a), len(b), sys.argv[1], len(diff), [hex(o) for o in diff[:6]]))
