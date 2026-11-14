"""Read-only (doppel_1411, 2026-11-14): words + relocations of one section (type:id) of a DRM, with external targets
named (type:id of the target section). 'pc:NAME' as sec_list.py.
Usage (from trudlcport): ../bin/pyt -t 600 work/doppel_1411/obj_relocs.py DRM TYPE:ID [MAXWORDS]"""
import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_write as DW, drm_reloc as R
from sec_list import raw_of


def main(a):
    D = DW.read(raw_of(a[0]), 'le')
    t, i = (int(x) for x in a[1].split(':'))
    n = int(a[2]) if len(a) > 2 else 64
    s = next(s for s in D.sections if (s.type, s.id) == (t, i))
    r = R.parse(bytes(s.reloc), 'le')
    it = dict(r.internal); ex = {so: (si, do) for si, so, do in r.external}
    ido = {o: ty for ty, o in r.idref}; ida = {o: ty for ty, o in r.idref_a}
    d = bytes(s.data)
    print('%d:%d size 0x%x internal %d external %d idref %d idref_a %d' % (t, i, len(d), len(it), len(ex), len(ido), len(ida)))
    for o in range(0, min(len(d), 4 * n) - 3, 4):
        w = struct.unpack_from('<I', d, o)[0]; note = ''
        if o in it: note = 'int -> +0x%x' % it[o]
        if o in ex:
            si, do = ex[o]; ts = D.sections[si]; note = 'ext -> #%d %d:%d +0x%x' % (si, ts.type, ts.id, do)
        if o in ido: note += ' idref type %d' % ido[o]
        if o in ida: note += ' idref_a type %d' % ida[o]
        print('  +0x%04x %08x %s' % (o, w, note))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
