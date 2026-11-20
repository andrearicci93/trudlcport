"""TruMenu 0.22.68 B2: negative copies of TruMenu.cpp for check_02268 (each with one rule broken).
Usage (from trudlcport): ../bin/pyt work/b2_2011/neg_copy.py   -> work/b2_2011/neg_<name>.cpp
Then: ../bin/pyt tools/trumenu_ini_check.py --cpp work/b2_2011/neg_<name>.cpp  (must print a Q02268 line)"""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CPP = os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'TruMenu.cpp')
CASES = [
    ('pushend', 'ThNotePushEnd(o.inst);', ''),
    ('index', 'ix[0] >= nv || ix[1] >= nv || ix[2] >= nv', 'ix[0] >= nv'),
    ('mismatch', '[Thor] MISMATCH pillar at ', '[Thor] pillar mismatch at '),
]


def main(argv):
    src = open(CPP, 'rb').read().decode('latin-1')
    for name, old, new in CASES:
        if src.count(old) < 1:
            print('%s: pattern not found' % name)
            return 1
        out = os.path.join(ROOT, 'work', 'b2_2011', 'neg_%s.cpp' % name)
        open(out, 'wb').write(src.replace(old, new, 1).encode('latin-1'))
        print('%s -> %s' % (name, out))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
