"""Read-only (doppel_1411, 2026-11-14): print the 8-byte condition records at given offsets of a chart DTP.
Usage (from trudlcport): ../bin/pyt -t 300 work/doppel_1411/cond_bytes.py DRM le|be SID OFF[,OFF..]"""
import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import drm_write as DW


def main(a):
    e = a[1]; f = '>' if e == 'be' else '<'
    D = DW.read(open(a[0], 'rb').read(), e)
    s = next(s for s in D.sections if s.type == 7 and s.id == int(a[2]))
    d = bytes(s.data)
    for o in (int(x, 16) for x in a[3].split(',')):
        k, i, v = struct.unpack_from(f + '3H', d, o)
        print('%s DTP %s +0x%05x: %s  = {%d,%d,%d} flags %d; value word at +0x%05x' % (
            os.path.basename(a[0]), a[2], o, d[o:o + 8].hex(' '), k, i, v, d[o + 6], o + 4))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
