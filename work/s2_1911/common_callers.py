"""Read-only: PC functions (int3-padding start heuristic of tools/pe_dis.py) that call ALL of the given addresses
(E8 rel32), with their size estimate and call counts (S2 analysis 2026-11-19: locate the PC twin of an Xbox function
from its mapped callees).

Usage (from the repository root):
  ../bin/pyt -t 300 work/s2_1911/common_callers.py EXE ADDR[,ADDR..] [--min K]   K = at least K of the addresses
"""
import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import pe_callers as PE
import pe_dis


def main(argv):
    exe = open(argv[0], 'rb').read()
    base, secs = PE.sections(exe)
    want = [int(x, 16) for x in argv[1].split(',')]
    k = int(argv[argv.index('--min') + 1]) if '--min' in argv else len(want)
    funcs = {}
    for name, sva, rptr, size, chars in secs:
        if not (chars & 0x20000000): continue
        blob = exe[rptr:rptr + size]
        for i in range(len(blob) - 5):
            if blob[i] != 0xe8: continue
            t = (sva + i + 5 + struct.unpack_from('<i', blob, i + 1)[0]) & 0xffffffff
            if t in want:
                fs = pe_dis.func_start(exe, secs, sva + i)
                funcs.setdefault(fs, {}).setdefault(t, []).append(sva + i)
    for fs in sorted(funcs):
        d = funcs[fs]
        if len(d) >= k:
            print('func 0x%08x: %s' % (fs, ', '.join('0x%x x%d' % (t, len(d[t])) for t in want if t in d)))


if __name__ == '__main__':
    main(sys.argv[1:])
