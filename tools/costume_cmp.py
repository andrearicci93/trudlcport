"""Compare the main DTPs (first 3 type-7 sections after the Object) of a DLC costume with every base lara_* / dlc_costume_* object (Xbox)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_write as DW
from rung1 import raw_pc, raw_xbox
from convert_dlc import raw_dlc
def main_dtps(d):
    return [s for s in d.sections if s.type == 7][:3]
if __name__ == '__main__':
    name = sys.argv[1]
    X = DW.read(raw_dlc(name)[0], 'be'); xd = main_dtps(X)
    print(name, [(s.id, len(s.data)) for s in xd], 'nsec', len(X.sections))
    for b in ['lara', 'lara_bikini', 'lara_casual', 'lara_doppelganger', 'lara_jungle_a', 'lara_jungle_b', 'lara_jungle_heavy', 'lara_mom_thrall',
              'lara_snow_heavy', 'lara_snow_light', 'lara_wetsuit_cold', 'lara_wetsuit_warm']:
        try: B = DW.read(raw_xbox(b + '.drm'), 'be')
        except Exception: continue
        bd = main_dtps(B); res = []
        for s, t in zip(xd, bd):
            if len(s.data) != len(t.data): res.append('size %d/%d' % (len(s.data), len(t.data))); continue
            n = len(s.data) // 4; diff = sum(s.data[4*i:4*i+4] != t.data[4*i:4*i+4] for i in range(n))
            res.append('diffw %d/%d reloc %s' % (diff, n, 'same' if s.reloc == t.reloc else 'differs'))
        print(' ', b, len(B.sections), res)
