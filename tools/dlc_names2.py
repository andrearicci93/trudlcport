"""Round 2 of DLC name recovery (after tools/dlc_names.py): music folders and images by generated patterns.
music: xenon-w\\music\\<P><unit>_<kind>_<NN>\\<same>.{mus,sam,mul}, P in dlc_/dlc1_/dlc2_/'', kind in mus/amb/visit_mus/...,
images: xenon-w\\image\\<stem>[_suffix].raw for stems of known DLC names. Updates work/generic/dlc_names.txt in place."""
import sys, os, re, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dlc_names import fcrc, W
lines = [l.rstrip('\n') for l in open(os.path.join(W, 'dlc_names.txt'))]
unk = {int(l.split()[0], 16) for l in lines if l.endswith(' ?')}
known = [l.split()[5] for l in lines if not l.endswith(' ?')]
units = set()
for f in ('dlc_pack11_unitlist.txt', 'dlc_pack10_unitlist.txt'):
    for l in open(os.path.join(W, 'lists', f), 'rb').read().decode('latin1').split('\r\n')[1:]:
        if l: units.add(l.split('\\')[-1].lower())
cores = set()
for u in units | {n.split('\\')[-1].rsplit('.', 1)[0] for n in known}:
    c = re.sub(r'^(dlc2?_|dlc1_)', '', u); cores.add(c)
    cores.add(re.sub(r'_(mus|amb|visit_mus)_\d+$', '', c))
for c in list(cores):
    t = c.split('_')
    for i in range(1, len(t) + 1):
        cores.add('_'.join(t[:i])); cores.add('_'.join(t[-i:]))
kinds = ['', 'intro', 'connector', 'theme', 'credits', 'puzzle', 'escape', 'boss', 'combat', 'chase', 'explore', 'tension', 'mus', 'amb', 'visit_mus', 'combat_mus', 'chase_mus', 'end_mus', 'stinger', 'ambience', 'music', 'cine_mus', 'boss_mus', 'fight_mus']
found = {}
for c in cores:
    for P in ('dlc_', 'dlc1_', 'dlc2_', '') + tuple('l%d_' % i for i in range(1, 10)):
        for k in kinds:
            for n in ['%02d' % i for i in range(1, 8)] + [str(i) for i in range(1, 8)] + ['']:
                d = P + c + ('_' + k if k else '') + ('_' + n if n else '')
                for e in ('mus', 'sam', 'mul'):
                    full = 'xenon-w\\music\\%s\\%s.%s' % (d, d, e)
                    h = fcrc(full)
                    if h in unk: found[h] = full
stems = {n.split('\\')[-1].rsplit('.', 1)[0] for n in known} | units | cores
for s in stems:
    for suf in ('', '_preview', '_hd', '_large', '_small', '_bg', '_loading', '_load', '_title', '_menu', '_icon', '_01', '_1'):
        for d in ('image', 'image\\dlc', 'cinstream'):
            for e in ('raw', 'mul', 'drm'):
                full = 'xenon-w\\%s\\%s%s.%s' % (d, s, suf, e)
                h = fcrc(full)
                if h in unk: found[h] = full
print('round2 found', len(found), sorted(set(found.values())))
out = []
for l in lines:
    h = int(l.split()[0], 16)
    if l.endswith(' ?') and h in found: l = l[:-1] + found[h]
    out.append(l)
open(os.path.join(W, 'dlc_names.txt'), 'w').write('\n'.join(out) + '\n')
print('still unnamed', sum(1 for l in out if l.endswith(' ?')))
