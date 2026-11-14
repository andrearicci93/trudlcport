"""Read-only (doppel_1411, 2026-11-14): differing words and pointer / id-reference differences of sections present in
two DRMs ('pc:NAME' as sec_list.py).
Usage (from trudlcport): ../bin/pyt -t 600 work/doppel_1411/sec_words.py A.drm B.drm TYPE:ID [TYPE:ID ..]"""
import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_write as DW, drm_reloc as R
from sec_list import raw_of


def main(a):
    DA = DW.read(raw_of(a[0]), 'le'); DB = DW.read(raw_of(a[1]), 'le')
    for spec in a[2:]:
        t, i = (int(x) for x in spec.split(':'))
        sa = next(s for s in DA.sections if (s.type, s.id) == (t, i))
        sb = next(s for s in DB.sections if (s.type, s.id) == (t, i))
        ra, rb = R.parse(bytes(sa.reloc), 'le'), R.parse(bytes(sb.reloc), 'le')
        print('== %d:%d size 0x%x / 0x%x' % (t, i, len(sa.data), len(sb.data)))
        for o in range(0, max(len(sa.data), len(sb.data)) - 3, 4):
            wa = struct.unpack_from('<I', sa.data, o)[0] if o + 4 <= len(sa.data) else None
            wb = struct.unpack_from('<I', sb.data, o)[0] if o + 4 <= len(sb.data) else None
            if wa != wb:
                print('  +0x%04x A %s B %s' % (o, '%08x' % wa if wa is not None else '--', '%08x' % wb if wb is not None else '--'))
        for name in ('internal', 'external', 'idref', 'idref_a'):
            xa, xb = sorted(getattr(ra, name)), sorted(getattr(rb, name))
            if xa != xb:
                print('  %s only A: %s' % (name, [x for x in xa if x not in xb]))
                print('  %s only B: %s' % (name, [x for x in xb if x not in xa]))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
