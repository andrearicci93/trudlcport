"""R8 helper (read-only on the game archives, 2026-11-18): copy the raw DRM of one PC base object / unit out of the
PC archives (patch first, then bigfile) to a local file, for the file-based tools (e.g. tools/markup_scan.py).
The copy is game data: write it to <workspace>/local_results/, never into the repository.

Usage (from the repository root):
  ../bin/pyt -t 300 work/r8_1811/drm_export.py NAME OUT.drm
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
import puzzle_switch_scan as PS
from names import crc


def main(argv):
    if len(argv) < 2:
        print(__doc__); return 2
    S = PS.Source('pc', None)
    h = crc(S.pre + '\\' + argv[0].lower() + '.drm')
    for a in S.arch:
        r = [x for x in a.find(h) if x['spec'] == 0xffffffff]
        if r:
            raw = a.read(r[0])
            open(argv[1], 'wb').write(raw)
            print('%s: %d bytes -> %s' % (argv[0], len(raw), argv[1]))
            return 0
    print('%s not found' % argv[0]); return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
