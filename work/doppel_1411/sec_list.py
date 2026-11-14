"""Read-only (doppel_1411, 2026-11-14): list sections of DRMs (type, id, size), optionally only some types / ids.
A DRM argument 'pc:NAME' reads pc-w\\NAME.drm from ../data/pc/bigfile.000.
Usage (from trudlcport): ../bin/pyt -t 600 work/doppel_1411/sec_list.py [--types 2,12] [--ids 4661] DRM [DRM ..]"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import drm_write as DW
from drm import cdrm_decode


def raw_of(p):
    if p.startswith('pc:'):
        from archive import Archive
        from names import crc
        pc = Archive('../data/pc/bigfile.000', 'le')
        r = pc.find(crc('pc-w\\%s.drm' % p[3:]))
        return cdrm_decode(pc.read(r[0]), 'le') if r else None
    return cdrm_decode(open(p, 'rb').read(), 'le')


def main(a):
    types = ids = None
    if '--types' in a: k = a.index('--types'); types = {int(x) for x in a[k + 1].split(',')}; del a[k:k + 2]
    if '--ids' in a: k = a.index('--ids'); ids = {int(x) for x in a[k + 1].split(',')}; del a[k:k + 2]
    for p in a:
        raw = raw_of(p)
        if raw is None: print('%s: not found' % p); continue
        D = DW.read(raw, 'le')
        hit = [(i, s) for i, s in enumerate(D.sections) if (types is None or s.type in types) and (ids is None or s.id in ids)]
        print('%s: %d sections, %d listed' % (os.path.basename(p), len(D.sections), len(hit)))
        for i, s in hit:
            print('  #%d type %d id %d size 0x%x' % (i, s.type, s.id, len(s.data)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
