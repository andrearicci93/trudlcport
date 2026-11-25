"""mr_save_items.py - (20/11/2026) solo lettura. Cosa appartiene a una unit in un salvataggio: blocchi 3/4 con unit di nascita = UNIT,
blocchi 2/5 con uid di un'intro della unit, dead bits sulle intro della unit, stickies kind 0 (owner = intro della unit) e kind 1
(owner = UNIT). Intro dalla baseline (DTP unit, record 0x90, uid a +0x58). uso: mr_save_items.py BASELINE UNIT.drm UNIT_ID SAVE..."""
import sys, struct, collections
sys.path.insert(0, '/path/to/trudlcport/tools'); sys.path.insert(0, '/path/to/trudlcport/work/ws/machine_room')
import drm, unit_ids, trusave as T
BL, U, UID = sys.argv[1], sys.argv[2], int(sys.argv[3])
names = {}
for l in open('/path/to/trudlcport/work/baseline/%s/mods/tr8/pc-w/objectlist.txt' % BL, errors='ignore'):
    p = l.split(',', 1)
    if len(p) == 2 and p[0].strip().isdigit(): names[int(p[0])] = p[1].strip()
h, S = drm.sections_with_data(drm.cdrm_decode(open('/path/to/trudlcport/work/baseline/%s/mods/%s' % (BL, U), 'rb').read(), 'le'), 'le')
intro = {}
for si, o in unit_ids.level_info(S, 'le')['intros']:
    d = S[si]['data']; intro[struct.unpack_from('<I', d, o + 0x58)[0]] = names.get(struct.unpack_from('<H', d, o + 0x50)[0], '?')
for f in sys.argv[4:]:
    d = open(f, 'rb').read(); base, ok = T.data_of(d); bl, end = T.blocks(d, base)
    print('==', f.split('/')[-1], 'CRC', ok)
    mine = [b for b in bl if (b[1] in (3, 4) and b[4] == UID) or (b[1] in (2, 5) and b[3] in intro) or (b[1] == 1 and b[3] == UID)]
    c = collections.Counter((b[1], intro.get(b[3], 'runtime' if b[3] and b[3] >= 0x40000000 else '?')) for b in mine)
    print('  blocchi della unit:', len(mine)); [print('    tipo %d %-34s x%d' % (k[0], k[1], v)) for k, v in sorted(c.items())]
    dd = sorted(u for u in T.dead(d, base) if u in intro); print('  dead bits della unit:', [(u, intro[u]) for u in dd])
    st = [s for s in T.stickies(d, base) if (s[4] == 0 and s[2] in intro) or (s[4] == 1 and s[2] == UID)]
    print('  stickies della unit:', len(st))
    for s in st: print('    %s #%d owner %d (%s) key %d kind %d = %s' % (s[0], s[1], s[2], intro.get(s[2], 'unit'), s[3], s[4], s[5]))
