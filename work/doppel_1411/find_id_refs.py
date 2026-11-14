"""Read-only (doppel_1411, 2026-11-14): sections of DRMs that hold an id reference (idref / idref_a relocation) or a
plain u32 word equal to the given section id ('pc:NAME' as sec_list.py).
Usage (from trudlcport): ../bin/pyt -t 600 work/doppel_1411/find_id_refs.py ID DRM [DRM ..]"""
import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_write as DW, drm_reloc as R
from sec_list import raw_of


def main(a):
    want = int(a[0])
    for p in a[1:]:
        D = DW.read(raw_of(p), 'le')
        for i, s in enumerate(D.sections):
            r = R.parse(bytes(s.reloc), 'le')
            ido = {o for _, o in r.idref} | {o for _, o in r.idref_a}
            d = bytes(s.data)
            for o in range(0, len(d) - 3, 4):
                if struct.unpack_from('<I', d, o)[0] == want:
                    print('%s #%d type %d id %d +0x%x%s' % (os.path.basename(p), i, s.type, s.id, o,
                                                         ' (id reference)' if o in ido else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
