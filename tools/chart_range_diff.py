"""Compare a range of state records (record-array indices) of one player state chart DTP between the Xbox original
(big-endian) and the converted PC file (little-endian): state ids, activities, transitions with their condition lists
(read-only; N10 2026-11-09, jump from a ledge to a rock vein: are records 1477..1505 of doppelganger_casual DTP 20212
converted 1:1?).

Records, transitions and conditions are read by tools/chart_state_path.py (Chart). A record is addressed by its index in
the record pointer array (= the transition target / parent index, as TruRockVein's chart log prints it).

Usage (from the repository root):
  ../bin/pyt -t 600 tools/chart_range_diff.py XBOX.drm PC.drm SID FROM TO [--all]
    prints every record of FROM..TO whose normalised text differs (--all: every record), Xbox line first ('X'),
    then the PC line ('P'); the last line is 'records A, differing B'. Exit code 0 = no difference, 1 = differences,
    2 = usage / load error.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chart_state_path as CP


def lines(C, idx):
    """normalised text of the record at record-array index idx (list of strings), or None"""
    ks = CP.targets(C, idx)
    if not ks:
        return None
    r, hdr, acts, sids, tr, l20 = C.state(ks[0])
    parent = hdr[3] - 0x10000 if hdr[3] & 0x8000 else hdr[3]
    out = ['%d parent %d sids %s' % (idx, parent, sids),
           '  acts ' + ' '.join('%d/t%d=%s' % (i, ty, CP.fmt_val(C.f, ty, v)) for i, ty, v in acts)]
    if l20:
        out.append('  +0x20 %s' % l20)
    for ti in tr:
        if ti >= len(C.tlist):
            out.append('  trans %d OUT OF RANGE' % ti)
            continue
        a, tg, w1, cnt, w3, conds = C.trans(ti)
        out.append('  -> %d [slot %d, w1 %d, w3 %d] %s%s' % (tg, ti, w1, w3,
                   'kinds %s ' % C.kinds(ti) if w1 else '', CP.fmt_conds(conds)))
    return out


def main():
    a = sys.argv[1:]
    show_all = '--all' in a
    a = [x for x in a if x != '--all']
    if len(a) != 5:
        print(__doc__)
        return 2
    try:
        X = CP.Chart(a[0], 'be', int(a[2]))
        P = CP.Chart(a[1], 'le', int(a[2]))
    except Exception as ex:
        print('load error: %s' % ex)
        return 2
    lo, hi = int(a[3]), int(a[4])
    print('Xbox %s: %d records, %d transitions; PC %s: %d records, %d transitions' % (
        a[0], len(X.recs), len(X.tlist), a[1], len(P.recs), len(P.tlist)))
    n = diff = 0
    for idx in range(lo, hi + 1):
        lx, lp = lines(X, idx), lines(P, idx)
        n += 1
        same = lx == lp
        if not same:
            diff += 1
        if same and not show_all:
            continue
        print('== record %d: %s' % (idx, 'same' if same else 'DIFFERENT'))
        if same:
            for s in lx or ['(none)']:
                print('   ' + s)
            continue
        for s in lx or ['(none)']:
            print('X  ' + s)
        for s in lp or ['(none)']:
            print('P  ' + s)
    print('records %d, differing %d' % (n, diff))
    return 1 if diff else 0


if __name__ == '__main__':
    sys.exit(main())
