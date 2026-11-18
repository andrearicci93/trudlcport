"""Read-only: print Lara state table entries (machine 1, 0x8b0a50, stride 28 B {id, slot 0..5}) for given state ids
from a `pe_dis.py --dwords 0x8b0a50 N` dump (R2 fall damage).

Usage (from the repository root):
  ../bin/pyt -t 60 work/r2_1811/states.py DWORDS.txt ID [ID ...]
"""
import sys


def main(argv):
    vals = []
    for line in open(argv[0], encoding='utf-8'):
        p = line.split()
        if len(p) == 2: vals.append(int(p[1], 16))
    want = set(int(x) for x in argv[1:])
    for k in range(len(vals) // 7):
        e = vals[7 * k:7 * k + 7]
        if e[0] in want:
            print('entry %3d @0x%08x id %4d  slots %s' % (k, 0x8b0a50 + 28 * k, e[0], ' '.join('0x%08x' % s for s in e[1:])))


if __name__ == '__main__':
    main(sys.argv[1:])
