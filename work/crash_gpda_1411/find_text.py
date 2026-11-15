"""Read-only: which sections of a DRM ('pc:<name>' = PC archive copy) contain the given ASCII strings.
Usage (repo root): ../bin/pyt work/crash_gpda_1411/find_text.py SPEC TEXT [...]"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from sec_hex import load


def main(argv):
    e, S = load(argv[0])
    for t in argv[1:]:
        b = t.encode('latin1')
        hits = ['%d:%d +0x%x' % (ty, i, d.find(b)) for ty, i, d, rl in S if d and b in d]
        print('%r: %s' % (t, hits[:10] or 'none'))


if __name__ == '__main__':
    main(sys.argv[1:])
