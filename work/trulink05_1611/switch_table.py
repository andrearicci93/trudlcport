"""TruLink 0.5 prep (2026-11-16): decode a compiler switch table of tru.exe (read-only).

Form: index = value - BIAS; byte = [BYTES + index] (when BYTES is given), target = [DWORDS + 4 * byte]. Prints
value -> target for every index 0..N-1, grouped by target (the default target = the most common one is marked).

Usage (from the repository root):
  ../bin/pyt -t 120 work/trulink05_1611/switch_table.py EXE BIAS N DWORDS [BYTES]   (hex numbers)
"""
import os, struct, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import pe_callers as PE


def main(argv):
    if len(argv) < 4:
        print(__doc__)
        return 2
    exe = open(argv[0], 'rb').read()
    base, secs = PE.sections(exe)
    bias, n, dwords = int(argv[1], 16), int(argv[2], 16), int(argv[3], 16)
    table = int(argv[4], 16) if len(argv) > 4 else None

    def off(a):
        for _, sva, rptr, size, _ in secs:
            if sva <= a < sva + size:
                return rptr + a - sva
        raise SystemExit('address 0x%x outside the sections' % a)

    targets = {}
    for i in range(n):
        k = exe[off(table + i)] if table is not None else i
        t = struct.unpack_from('<I', exe, off(dwords + 4 * k))[0]
        targets.setdefault(t, []).append(i + bias)
    common = max(targets, key=lambda t: len(targets[t]))
    for t in sorted(targets):
        vals = targets[t]
        print('0x%08x%s: %s' % (t, ' (default)' if t == common and len(vals) > 3 else '',
                                ' '.join('0x%x' % v for v in vals) if len(vals) <= 24 else '%d values' % len(vals)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
