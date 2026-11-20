"""A2 (2026-11-20): convert raw file offsets of a 32-bit PE (tru.exe) to virtual addresses and back (read only).

Usage (from the repository root):
  ../bin/pyt -t 60 work/a2_2011/a2_off2va.py EXE off2va OFF[,OFF..]
  ../bin/pyt -t 60 work/a2_2011/a2_off2va.py EXE va2off VA[,VA..]
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import pe_callers as PE


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    exe = open(argv[0], 'rb').read()
    base, secs = PE.sections(exe)
    for s in argv[2].split(','):
        x = int(s, 16)
        hit = None
        for sec in secs:
            name, sva, rptr, size = sec[0], sec[1], sec[2], sec[3]
            if argv[1] == 'off2va' and rptr <= x < rptr + size:
                hit = (name, sva + x - rptr)
            if argv[1] == 'va2off' and sva <= x < sva + size:
                hit = (name, rptr + x - sva)
        print('0x%08x -> %s' % (x, ('0x%08x (%s)' % (hit[1], hit[0])) if hit else 'outside'))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
