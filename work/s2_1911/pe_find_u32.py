"""Read-only: find aligned little-endian 32-bit values in the sections of a 32-bit PE (tru.exe) and print their virtual
addresses (S2 analysis 2026-11-19: float constants of a function, to locate its PC twin by anchors).

Usage (from the repository root):
  ../bin/pyt -t 300 work/s2_1911/pe_find_u32.py EXE VALUE_HEX[,VALUE_HEX..] [--any]   --any = also unaligned
"""
import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import pe_callers as PE


def main(argv):
    exe = open(argv[0], 'rb').read()
    base, secs = PE.sections(exe)
    anyal = '--any' in argv
    for s in argv[1].split(','):
        v = int(s, 16)
        pat = struct.pack('<I', v)
        hits = []
        for name, sva, rptr, size, _ in secs:
            blob = exe[rptr:rptr + size]
            i = blob.find(pat)
            while i >= 0:
                if anyal or i % 4 == 0: hits.append('%s:0x%08x' % (name, sva + i))
                i = blob.find(pat, i + 1)
        print('0x%08x %d hits: %s' % (v, len(hits), ' '.join(hits[:30])))


if __name__ == '__main__':
    main(sys.argv[1:])
