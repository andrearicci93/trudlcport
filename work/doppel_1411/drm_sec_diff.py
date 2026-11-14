"""Read-only (doppel_1411, 2026-11-14): section-by-section diff of two DRMs keyed by (type, id, occurrence):
only in A / only in B / differing (size, words, internal / external pointers, id references). 'pc:NAME' as sec_list.py.
Usage (from trudlcport): ../bin/pyt -t 600 work/doppel_1411/drm_sec_diff.py A.drm B.drm [--types 0,7,11,12]"""
import sys, os, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_write as DW, drm_reloc as R
from sec_list import raw_of


def keyed(D):
    occ = collections.Counter(); out = collections.OrderedDict()
    for i, s in enumerate(D.sections):
        k = (s.type, s.id, occ[(s.type, s.id)]); occ[(s.type, s.id)] += 1; out[k] = (i, s)
    return out


def main(a):
    types = None
    if '--types' in a: k = a.index('--types'); types = {int(x) for x in a[k + 1].split(',')}; del a[k:k + 2]
    A = keyed(DW.read(raw_of(a[0]), 'le')); B = keyed(DW.read(raw_of(a[1]), 'le'))
    sel = lambda ks: [k for k in ks if types is None or k[0] in types]
    oa = sel([k for k in A if k not in B]); ob = sel([k for k in B if k not in A])
    print('A %s: %d sections; B %s: %d sections' % (a[0], len(A), a[1], len(B)))
    print('only in A (%d): %s' % (len(oa), ' '.join('%d:%d' % k[:2] for k in oa)))
    print('only in B (%d): %s' % (len(ob), ' '.join('%d:%d' % k[:2] for k in ob)))
    nd = 0
    for k in sel([k for k in A if k in B]):
        (ia, sa), (ib, sb) = A[k], B[k]
        ra, rb = R.parse(bytes(sa.reloc), 'le'), R.parse(bytes(sb.reloc), 'le')
        w = sum(1 for o in range(0, min(len(sa.data), len(sb.data)) - 3, 4) if sa.data[o:o + 4] != sb.data[o:o + 4])
        same = (len(sa.data) == len(sb.data) and w == 0 and sorted(ra.internal) == sorted(rb.internal)
                and sorted(ra.external) == sorted(rb.external) and sorted(ra.idref) == sorted(rb.idref)
                and sorted(ra.idref_a) == sorted(rb.idref_a))
        if same: continue
        nd += 1
        print('DIFF %d:%d  #%d/#%d  size 0x%x/0x%x  words %d  int %d/%d  ext %d/%d  idref %d/%d' % (
            k[0], k[1], ia, ib, len(sa.data), len(sb.data), w, len(ra.internal), len(rb.internal), len(ra.external),
            len(rb.external), len(ra.idref) + len(ra.idref_a), len(rb.idref) + len(rb.idref_a)))
    print('differing shared sections: %d' % nd)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
