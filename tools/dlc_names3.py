"""Round 3: VO / stream paths. DLC data hold strings like 'vo\\dlc2\\doppelganger\\I_DG_PDLC2_MACH_08' (relative to
xenon-w\\audio\\streams\\); try them + every trailing-number variant (01..40) + sibling folders. Updates dlc_names.txt."""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dlc_names import fcrc, W, PACKS
from archive import Archive
from drm import cdrm_decode
lines = [l.rstrip('\n') for l in open(os.path.join(W, 'dlc_names.txt'))]
unk = {int(l.split()[0], 16) for l in lines if l.endswith(' ?')}
strs = set()
for pk, p in PACKS.items():
    A = Archive(p, 'be')
    for r in A.idx:
        b = A.read(r)
        if b[:4] == b'CDRM': b = cdrm_decode(b, 'be')
        for m in re.findall(rb'[A-Za-z0-9_]*\\[A-Za-z0-9_\\]+', b):
            strs.add(m.decode('latin1').lower().strip('\\'))
print('path-like strings', len(strs))
cands = set()
for s in strs:
    cands.add(s)
    m = re.match(r'(.*?)(\d+)$', s)
    if m:
        w = len(m.group(2))
        for i in range(0, 60): cands.add(m.group(1) + str(i).zfill(w))
dirs = set(s.rsplit('\\', 1)[0] for s in strs if '\\' in s)
found = {}
for c in cands:
    for pre in ('xenon-w\\audio\\streams\\', 'xenon-w\\audio\\', 'xenon-w\\', 'xenon-w\\cinstream\\', 'xenon-w\\music\\'):
        for e in ('.mul', '.sam', '.mus', '.raw', '.drm', ''):
            h = fcrc(pre + c + e)
            if h in unk: found[h] = pre + c + e
print('round3 found', len(found)); [print('  ', v) for v in sorted(set(found.values()))]
out = []
for l in lines:
    h = int(l.split()[0], 16)
    if l.endswith(' ?') and h in found: l = l[:-1] + found[h]
    out.append(l)
open(os.path.join(W, 'dlc_names.txt'), 'w').write('\n'.join(out) + '\n')
print('still unnamed records', sum(1 for l in out if l.endswith(' ?')), 'distinct', len({l.split()[0] for l in out if l.endswith(' ?')}))
