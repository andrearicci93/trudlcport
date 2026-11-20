"""TruMenu 0.22.67 B1: negative copies of TruMenu.cpp for check_02267 (each with one rule broken).
Usage (from trudlcport): ../bin/pyt work/b1_2011/neg_copy.py   -> work/b1_2011/neg_<n>.cpp"""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CPP = os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'TruMenu.cpp')
CASES = [
    ('gate', 'if (K1Gate("level.load", o, n)) return false;', ''),
    ('chain', 'p.chain = vt == 58 && st == 1 && !PzSwUsed(inst)', 'p.chain = vt == 58 && st == 1'),
    ('lift', '[Perch] LIFT', '[Perch] UP'),
    ('world', 'B1ToWorld(irot[2], vLocal, v);', 'memcpy(v, vLocal, sizeof(v));'),
]


def main(argv):
    src = open(CPP, 'rb').read().decode('latin-1')
    for name, old, new in CASES:
        if src.count(old) < 1:
            print('%s: pattern not found' % name)
            return 1
        out = os.path.join(ROOT, 'work', 'b1_2011', 'neg_%s.cpp' % name)
        open(out, 'wb').write(src.replace(old, new, 1).encode('latin-1'))
        print('%s -> %s' % (name, out))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
