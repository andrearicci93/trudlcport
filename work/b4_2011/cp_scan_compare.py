"""B4 2011 (TruMenu 0.22.69 point 1): compare the checkpoint table of truintro::ScanCheckpoints (selftest
TruCpScanTest.exe) with the table of tools/unit_checkpoint_table.py, read only.

Usage (from trudlcport):
  ../bin/pyt work/b4_2011/cp_scan_compare.py PYTHON_TABLE CPP_TABLE
Rows "<unit> <intro id> # ... at x y z ..."; '#' lines are comments. Compared: the set of (unit, id) pairs and the
position of each pair (0.05 units).
Exit code: 0 = the same pairs and positions, 1 = differences (listed), 2 = usage / unreadable file.
"""
import sys


def rows(path):
    out = {}
    for line in open(path, 'r', encoding='latin1'):
        if line.startswith('#'):
            continue
        head, _, tail = line.partition('#')
        w = head.split()
        if len(w) < 2:
            continue
        pos = None
        t = tail.split()
        if 'at' in t:
            i = t.index('at')
            try:
                pos = tuple(float(x.rstrip(';')) for x in t[i + 1:i + 4])
            except ValueError:
                pos = None
        out[(w[0].lower(), int(w[1]))] = pos
    return out


def main(a):
    if len(a) != 2:
        print(__doc__)
        return 2
    try:
        p, c = rows(a[0]), rows(a[1])
    except (OSError, ValueError) as ex:
        print('cannot read: %s' % ex)
        return 2
    bad = 0
    for k in sorted(set(p) | set(c)):
        if k not in p or k not in c:
            bad += 1
            print('%-28s %6d only in %s' % (k[0], k[1], 'python' if k in p else 'cpp'))
            continue
        pp, cp = p[k], c[k]
        if not pp or not cp or max(abs(x - y) for x, y in zip(pp, cp)) > 0.05:
            bad += 1
            print('%-28s %6d position python %s cpp %s' % (k[0], k[1], pp, cp))
    print('%d checkpoint(s) python, %d cpp, %d difference(s)' % (len(p), len(c), bad))
    return 1 if bad or not p else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
