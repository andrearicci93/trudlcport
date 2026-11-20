"""A2 (2026-11-20): decode an MSVC two-level switch in tru.exe (read only): case value v = BASE + i for i in 0..N-1,
byte index table IDX[i] -> dword target table TAB[IDX[i]]. Prints the case values per target (optionally only the
targets given).

Usage (from the repository root):
  ../bin/pyt -t 60 work/a2_2011/a2_jtab.py EXE IDX_HEX TAB_HEX N BASE [TARGET_HEX,..]
"""
import sys, os, struct, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import pe_callers as PE


def va_off(secs, va):
    for sec in secs:
        if sec[1] <= va < sec[1] + sec[3]:
            return sec[2] + va - sec[1]
    return -1


def main(argv):
    if len(argv) < 5:
        print(__doc__)
        return 2
    exe = open(argv[0], 'rb').read()
    base, secs = PE.sections(exe)
    idx, tab, n, b0 = int(argv[1], 16), int(argv[2], 16), int(argv[3]), int(argv[4], 0)
    want = set(int(x, 16) for x in argv[5].split(',')) if len(argv) > 5 else None
    oi, ot = va_off(secs, idx), va_off(secs, tab)
    by = collections.defaultdict(list)
    for i in range(n):
        k = exe[oi + i]
        t = struct.unpack_from('<I', exe, ot + 4 * k)[0]
        by[t].append(b0 + i)
    for t in sorted(by):
        if want is not None and t not in want:
            continue
        print('0x%08x: %s' % (t, ' '.join('0x%x' % v for v in by[t])))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
