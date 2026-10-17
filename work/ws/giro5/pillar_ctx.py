import sys, struct
sys.path.insert(0, '/path/to/trudlcport/tools'); sys.path.insert(0, '/path/to/trudlcport/work/ws/giro5')
import drm
from archive import Archive
from names import load, L
R = '/path/to/trudlcport/work/baseline/B87_materiali19/mods/'
pc = {s['id']: s for s in drm.sections_with_data(drm.cdrm_decode(open(R + 'dlc1_uo_pillar_of_doom_a.drm', 'rb').read(), 'le'), 'le')[1] if s['type'] == 7}
C = '/path/to/Xenia-SteveRepack/Content/534307EC/00000002/'; xn = load(L + 'Tomb Raider Underworld (Xenon).txt')
xb = None
for pk in [C + '9CA70CF0EDA43654D158C2E37470D301DFA850E753/pack10.000', C + '600A12643FCDAC84003E6E0DBD0A1A8F7DAE9DD153/pack11.000']:
    A = Archive(pk, 'be')
    for r in A.idx:
        if xn.get(r['hash'], '').split('\\')[-1] == 'dlc1_uo_pillar_of_doom_a.drm':
            xb = {s['id']: s for s in drm.sections_with_data(drm.cdrm_decode(A.read(r), 'be'), 'be')[1] if s['type'] == 7}
print('PC DTP ids', sorted(pc)); print('Xbox DTP ids', sorted(xb))
p = pc[21176]['data']
for id_x in sorted(xb):
    x = xb[id_x]['data']
    if len(x) == len(p):
        print('Xbox DTP', id_x, 'stessa dimensione', len(x))
        for o in range(0x170, 0x1a0, 4): print('  %#x X %08x  PC(LE as u32) %08x' % (o, struct.unpack_from('>I', x, o)[0], struct.unpack_from('<I', p, o)[0]))
