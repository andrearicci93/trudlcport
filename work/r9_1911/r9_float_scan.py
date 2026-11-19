"""R9 (2026-11-19): where does a float of about LO..HI live? Scans a PE (little-endian, every section's raw data) or an
Xbox memory image (big-endian, whole file) for 4-byte floats (and 8-byte doubles at 4-aligned offsets) in [LO, HI].
Read-only; prints address and value only.

Usage (from the repository root):
  ../bin/pyt -t 600 work/r9_1911/r9_float_scan.py --pe EXE LO HI
  ../bin/pyt -t 600 work/r9_1911/r9_float_scan.py --xbox IMAGE.bin LO HI
"""
import sys, os, struct, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import pe_callers as PE


def scan(buf, start, end, f, lo, hi, va_of):
    out = []
    for o in range(start, end - 3, 4):
        v = struct.unpack_from(f + 'f', buf, o)[0]
        if lo <= v <= hi:
            out.append(('f32', va_of(o), v))
        if o + 8 <= end:
            d = struct.unpack_from(f + 'd', buf, o)[0]
            if lo <= d <= hi and not math.isnan(d):
                out.append(('f64', va_of(o), d))
    return out


def main(argv):
    if len(argv) != 4:
        sys.exit(__doc__)
    mode, path, lo, hi = argv[0], argv[1], float(argv[2]), float(argv[3])
    buf = open(path, 'rb').read()
    res = []
    if mode == '--pe':
        base, secs = PE.sections(buf)
        for name, sva, rptr, size, chars in secs:
            for k, va, v in scan(buf, rptr, rptr + size, '<', lo, hi, lambda o, s=sva, r=rptr: s + o - r):
                res.append((k, va, v, name))
    else:
        for k, va, v in scan(buf, 0, len(buf), '>', lo, hi, lambda o: 0x82000000 + o):
            res.append((k, va, v, ''))
    for k, va, v, name in res:
        print('%s 0x%08x %.6f %s' % (k, va, v, name))
    print('hits %d' % len(res))


if __name__ == '__main__':
    main(sys.argv[1:])
