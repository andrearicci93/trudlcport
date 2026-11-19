"""T2 1911 (TruMenu 0.22.66 point 2): compare the intro table of TruIntroScan.h (selftest TruIntroScanTest.exe) with the
table of tools/unit_intro_table.py, read only.

Usage (from trudlcport):
  ../bin/pyt work/t2_1911/intro_scan_compare.py PYTHON_TABLE CPP_TABLE
Rows "<intro id> <own unit> # ..." ('-' = no own unit, skipped as TruMenu cannot use it); '#' lines are comments.
Exit code: 0 = the same {intro: own unit} pairs, 1 = differences (listed), 2 = usage / unreadable file.
"""
import sys


def rows(path):
    out = {}
    for line in open(path, 'r', encoding='latin1'):
        line = line.split('#', 1)[0].split()
        if len(line) < 2 or line[1] == '-':
            continue
        out[int(line[0])] = line[1].lower()
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
        pv, cv = p.get(k), c.get(k)
        state = 'ok' if pv == cv else 'DIFF'
        bad += pv != cv
        print('%-6d python %-22s cpp %-22s %s' % (k, pv or '(none)', cv or '(none)', state))
    print('%d intro(s) python, %d cpp, %d difference(s)' % (len(p), len(c), bad))
    return 1 if bad or not p else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
