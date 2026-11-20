"""Read-only: print a two-level switch (byte map + dword jump table) of a 32-bit PE such as tru.exe
(A4 analysis 2026-11-20: message handlers of the portable / holder classes).

Usage (from the repository root):
  ../bin/pyt -t 120 work/a4_2011/jumpmap.py EXE BYTEMAP_VA JUMPTABLE_VA BASE COUNT [--skip-default]
    case value v = BASE + i for i in [0, COUNT); target = dword [JUMPTABLE + 4 * byte [BYTEMAP + i]]
    --skip-default: leave out the cases that go to the most frequent target (the default)
  ../bin/pyt -t 120 work/a4_2011/jumpmap.py EXE --table JUMPTABLE_VA BASE COUNT
    one-level table: target = dword [JUMPTABLE + 4 * i]
"""
import sys, os, struct
from collections import Counter
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import pe_callers as PE


def off_of(secs, a):
    for _, sva, rptr, size, _ in secs:
        if sva <= a < sva + size:
            return rptr + a - sva
    raise SystemExit('address 0x%x not in a section' % a)


def main(argv):
    exe = open(argv[0], 'rb').read()
    _, secs = PE.sections(exe)
    rows = []
    if argv[1] == '--table':
        jt, base, n = int(argv[2], 16), int(argv[3], 16), int(argv[4], 16)
        for i in range(n):
            rows.append((base + i, struct.unpack_from('<I', exe, off_of(secs, jt + 4 * i))[0]))
        skip = '--skip-default' in argv
    else:
        bm, jt, base, n = (int(x, 16) for x in argv[1:5])
        for i in range(n):
            k = exe[off_of(secs, bm + i)]
            rows.append((base + i, struct.unpack_from('<I', exe, off_of(secs, jt + 4 * k))[0]))
        skip = '--skip-default' in argv
    default = Counter(t for _, t in rows).most_common(1)[0][0]
    print('default target 0x%08x (%d cases)' % (default, sum(1 for _, t in rows if t == default)))
    for v, t in rows:
        if skip and t == default:
            continue
        print('case 0x%04x -> 0x%08x' % (v, t))


if __name__ == '__main__':
    main(sys.argv[1:])
