"""A1 (2026-11-20): records of a state chart DTP whose activity list holds a given activity id and / or whose
formatted activity value contains a text (e.g. 316.056). Read only.

Usage (from the repository root):
  ../bin/pyt -t 300 work/a1_2011/a1_act_find.py DRM ENDIAN SID [--id N] [--val TEXT]
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import chart_state_path as CP


def main():
    a = sys.argv[1:]
    if len(a) < 3:
        print(__doc__)
        return 2
    want_id = None
    want_val = None
    if '--id' in a:
        want_id = int(a[a.index('--id') + 1])
    if '--val' in a:
        want_val = a[a.index('--val') + 1]
    C = CP.Chart(a[0], a[1], int(a[2]))
    hits = 0
    for idx in range(len(C.recs)):
        ks = CP.targets(C, idx)
        if not ks:
            continue
        r, hdr, acts, sids, tr, l20 = C.state(ks[0])
        for i, ty, v in acts:
            txt = CP.fmt_val(C.f, ty, v)
            if want_id is not None and i != want_id:
                continue
            if want_val is not None and want_val not in txt:
                continue
            parent = hdr[3] - 0x10000 if hdr[3] & 0x8000 else hdr[3]
            print('%d: parent %d sids %s act %d/t%d=%s' % (idx, parent, sids, i, ty, txt))
            hits += 1
    print('hits %d' % hits)
    return 0


if __name__ == '__main__':
    sys.exit(main())
