"""Read-only: find 32-bit values in a raw image file (Xbox big-endian Xenia image with base 0x82000000, or any file
with a given base) and print the address of every hit plus the surrounding dwords (S2 analysis 2026-11-19: state
table entries that hold a handler address).

Usage (from the repository root):
  ../bin/pyt -t 300 work/s2_1911/find_u32.py FILE BASE_HEX be|le VALUE_HEX[,VALUE_HEX..] [CONTEXT_DWORDS]
"""
import sys, struct


def main(argv):
    data = open(argv[0], 'rb').read()
    base = int(argv[1], 16)
    fmt = '>I' if argv[2] == 'be' else '<I'
    ctx = int(argv[4]) if len(argv) > 4 else 4
    for s in argv[3].split(','):
        v = int(s, 16)
        pat = struct.pack(fmt, v)
        i = data.find(pat)
        n = 0
        while i >= 0 and n < 40:
            if i % 4 == 0:
                lo = max(0, i - 4 * ctx)
                words = [struct.unpack_from(fmt, data, o)[0] for o in range(lo, min(len(data) - 3, i + 4 * ctx + 4), 4)]
                print('0x%08x hit 0x%08x at 0x%08x: %s' % (v, v, base + i,
                      ' '.join(('[%08x]' if lo + 4 * k == i else '%08x') % w for k, w in enumerate(words))))
                n += 1
            i = data.find(pat, i + 1)
        if n == 0: print('0x%08x: no aligned hit' % v)


if __name__ == '__main__':
    main(sys.argv[1:])
