"""Read-only: every PowerPC `b` / `bl` (opcode 18, relative) in an Xbox 360 Xenia image (base 0x82000000) whose target
is one of the given addresses - including tail branches `b`, which tools/ppc_xrefs.py does not list as callers
(S2 analysis 2026-11-19: who reaches the balance-beam helpers).

Usage (from the repository root):
  ../bin/pyt -t 300 work/s2_1911/ppc_branch_to.py IMAGE.bin ADDR[,ADDR..]
"""
import sys, struct


def main(argv):
    data = open(argv[0], 'rb').read()
    base = 0x82000000
    want = set(int(x, 16) for x in argv[1].split(','))
    lo, hi = 0x82080000 - base, min(len(data), 0x82800000 - base)
    for o in range(lo, hi - 3, 4):
        w = struct.unpack_from('>I', data, o)[0]
        if (w >> 26) != 18 or (w & 2): continue
        d = w & 0x03fffffc
        if d & 0x02000000: d -= 0x04000000
        t = (base + o + d) & 0xffffffff
        if t in want:
            print('0x%08x %s -> 0x%08x' % (base + o, 'bl' if w & 1 else 'b ', t))


if __name__ == '__main__':
    main(sys.argv[1:])
