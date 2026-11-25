"""intro_vs_live.py - (20/11/2026) solo lettura. Intro della unit (baseline, DTP unit Level+0x74, record 0x90) contro le istanze vive di
un dump (list_inst.py): per ogni intro pos/oggetto/uid (+0x58) e se l'istanza con quell'uid e' viva. uso: intro_vs_live.py BASELINE UNIT.drm INST.txt"""
import sys, struct, re, collections
sys.path.insert(0, '/path/to/trudlcport/tools')
import unit_ids
import drm
BL, U, IT = sys.argv[1:4]
names = {}
for l in open('/path/to/trudlcport/work/baseline/%s/mods/tr8/pc-w/objectlist.txt' % BL, errors='ignore'):
    p = l.split(',', 1)
    if len(p) == 2 and p[0].strip().isdigit(): names[int(p[0])] = p[1].strip()
live = {}
for l in open(IT, encoding='utf-8', errors='ignore'):
    m = re.search(r'uid=\s*(\d+) pos=\(\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\)', l)
    if m: live[int(m.group(1))] = (l[:8], tuple(float(m.group(k)) for k in (2, 3, 4)), l[14:42].strip())
h, secs = drm.sections_with_data(drm.cdrm_decode(open('/path/to/trudlcport/work/baseline/%s/mods/%s' % (BL, U), 'rb').read(), 'le'), 'le'); L = unit_ids.level_info(secs, 'le')
c = collections.Counter(); out = []
for si, o in L['intros']:
    d = secs[si]['data']; pos = struct.unpack_from('<3f', d, o); oid = struct.unpack_from('<H', d, o + 0x50)[0]
    uid = struct.unpack_from('<I', d, o + 0x58)[0]; nm = names.get(oid, '?'); v = uid in live
    c[nm, v] += 1
    out.append('%s %5d %-36s uid=%6d pos=(%8.1f %8.1f %8.1f)%s' % ('VIVA ' if v else 'nonviva', oid, nm[:36], uid, *pos, '  live pos=(%.1f %.1f %.1f)' % live[uid][1] if v else ''))
print('\n'.join(sorted(out, key=lambda s: s[14:52])))
print('--- per oggetto (viva/non viva)')
for nm in sorted({k[0] for k in c}): print('%-36s viva %3d  non viva %3d' % (nm, c[nm, True], c[nm, False]))
