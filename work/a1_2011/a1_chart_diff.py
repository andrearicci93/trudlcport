"""A1 (2026-11-20): chart_range_diff with different section ids on the two sides (base Lara chart: Xbox DTP 12647,
PC DTP 850). Read only; prints 'record N same / DIFFERENT' per record of FROM..TO and a summary line.

Usage (from the repository root):
  ../bin/pyt -t 600 work/a1_2011/a1_chart_diff.py XBOX.drm XSID PC.drm PSID FROM TO [FROM TO ...] [--noslot]
    --noslot: ignore transition slot numbers (each file's own pointer-array position)
Exit code 0 = all equal, 1 = differences, 2 = usage / load error.
"""
import sys, os, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import chart_state_path as CP
import chart_range_diff as RD


def main():
    a = [x for x in sys.argv[1:] if x != '--noslot']
    if len(a) < 6 or (len(a) - 4) % 2:
        print(__doc__)
        return 2
    try:
        X = CP.Chart(a[0], 'be', int(a[1]))
        P = CP.Chart(a[2], 'le', int(a[3]))
    except Exception as ex:
        print('load error: %s' % ex)
        return 2
    print('Xbox %s DTP %s: %d records; PC %s DTP %s: %d records' % (a[0], a[1], len(X.recs), a[2], a[3], len(P.recs)))
    n = diff = 0
    rest = a[4:]
    for k in range(0, len(rest), 2):
        lo, hi = int(rest[k]), int(rest[k + 1])
        for idx in range(lo, hi + 1):
            lx, lp = RD.lines(X, idx), RD.lines(P, idx)
            if '--noslot' in sys.argv:
                # transition slot numbers are positions in each file's own pointer array, not content
                lx = [re.sub(r'slot \d+, ', '', s) for s in (lx or [])]
                lp = [re.sub(r'slot \d+, ', '', s) for s in (lp or [])]
            n += 1
            if lx == lp:
                continue
            diff += 1
            print('== record %d: DIFFERENT' % idx)
            for s in lx or ['(none)']:
                print('  X ' + s)
            for s in lp or ['(none)']:
                print('  P ' + s)
    print('records %d, differing %d' % (n, diff))
    return 1 if diff else 0


if __name__ == '__main__':
    sys.exit(main())
