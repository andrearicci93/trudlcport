"""TruMenu 0.22.67 B1: move the B1 section (start marker .. end marker, inclusive) from before MdTick to after
MdDrawArcs (before the Thor section), so the 0.22.65 [Perch] section (up to MdTick) stays read only.
Usage (from trudlcport): ../bin/pyt work/b1_2011/move_b1_block.py [--dry]
Keeps the file's bytes otherwise (CRLF / LF as found)."""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CPP = os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'TruMenu.cpp')
START = b'// ======================================================================================================================\n// ---- 0.22.67 B1 (package B1'
END = b'// ---- end of 0.22.67 B1 (the puzzle parts V1 / N5 sit in the puzzle sections) ----\n'
TARGET = b'// ---- 0.22.61 (package R1c point 1) Thor pillar floor areas'


def main(argv):
    data = open(CPP, 'rb').read()
    crlf = b'\r\n' in data[:4000]
    nl = b'\r\n' if crlf else b'\n'
    start = START.replace(b'\n', nl)
    end = END.replace(b'\n', nl)
    a = data.find(start)
    b = data.find(end, a)
    if a < 0 or b < 0 or data.find(start, a + 1) >= 0:
        print('markers not found exactly once (start %d, end %d)' % (a, b))
        return 1
    b += len(end)
    block = data[a:b]
    rest = data[:a] + data[b:]
    t = rest.find(TARGET)
    if t < 0 or rest.find(TARGET, t + 1) >= 0:
        print('target marker not found exactly once')
        return 1
    if t < a:
        print('target lies before the block - nothing done')
        return 1
    out = rest[:t] + block + rest[t:]
    print('block %d bytes, %d lines; moved from offset %d to %d; size %d -> %d' % (len(block), block.count(b'\n'), a, t,
                                                                                 len(data), len(out)))
    if '--dry' in argv:
        return 0
    open(CPP, 'wb').write(out)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
