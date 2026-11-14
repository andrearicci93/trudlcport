"""Read-only (doppel_1411, 2026-11-14): compare one section (type, id) of two DRMs: size, internal pointers and words in
an offset window. 'pc:NAME' = pc-w\\NAME.drm from ../data/pc/bigfile.000.
Usage (from trudlcport): ../bin/pyt -t 600 work/doppel_1411/sec_cmp.py A.drm B.drm TYPE ID FROM TO"""
import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_write as DW, drm_reloc as R
from sec_list import raw_of


def sec(p, t, i):
    D = DW.read(raw_of(p), 'le')
    return next(s for s in D.sections if s.type == t and s.id == i)


def main(a):
    t, i, lo, hi = int(a[2]), int(a[3]), int(a[4], 16), int(a[5], 16)
    S = [sec(a[0], t, i), sec(a[1], t, i)]
    R_ = [R.parse(bytes(s.reloc), 'le') for s in S]
    for k, (s, r) in enumerate(zip(S, R_)):
        it = dict(r.internal)
        print('%s: size 0x%x, %d internal, %d external, %d idref; header +0..+0x40: %s' % (
            os.path.basename(a[k]), len(s.data), len(r.internal), len(r.external), len(r.idref) + len(r.idref_a),
            bytes(s.data[:0x40]).hex(' ')))
    ia, ib = dict(R_[0].internal), dict(R_[1].internal)
    ea = {src: (si, dst) for si, src, dst in R_[0].external}; eb = {src: (si, dst) for si, src, dst in R_[1].external}
    print('offset    A word    B word    A ptr        B ptr')
    for o in range(lo, min(hi, len(S[0].data), len(S[1].data)), 4):
        wa = struct.unpack_from('<I', S[0].data, o)[0]; wb = struct.unpack_from('<I', S[1].data, o)[0]
        pa = ('int->0x%x' % ia[o]) if o in ia else (('ext %s' % (ea[o],)) if o in ea else '-')
        pb = ('int->0x%x' % ib[o]) if o in ib else (('ext %s' % (eb[o],)) if o in eb else '-')
        print('+0x%05x %08x  %08x  %-12s %-12s%s' % (o, wa, wb, pa, pb, '' if (wa, pa) == (wb, pb) else '   <- differs'))
    da = [o for o in range(0, min(len(S[0].data), len(S[1].data)) - 3, 4)
          if S[0].data[o:o + 4] != S[1].data[o:o + 4]]
    print('words differing in the whole section: %d; pointer sets equal: %s' % (len(da), ia == ib and ea == eb))
    only_a = sorted(set(ia) - set(ib)); only_b = sorted(set(ib) - set(ia))
    print('internal pointers only in A: %d %s; only in B: %d %s' % (len(only_a), [hex(x) for x in only_a[:12]],
                                                                    len(only_b), [hex(x) for x in only_b[:12]]))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
