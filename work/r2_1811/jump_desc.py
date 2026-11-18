"""Read-only: dump the jump descriptor table of a player object DRM (player data block P = target of the relocated
pointer +0xc8; P+0xde4 count, P+0xde8 -> array of {u32 id, X*}; lookup 0x6f1950) with each record's words as float /
int (R11 jump preview and catch tolerance, 2026-11-18).

Usage (from the repository root):
  ../bin/pyt -t 300 work/r2_1811/jump_desc.py DRM ENDIAN [LEN_HEX]     LEN default 0xe0 bytes per record
"""
import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import player_block_fix as PB
import drm_write as DW
import drm_reloc as R


def main(argv):
    path, e = argv[0], argv[1]
    ln = int(argv[2], 16) if len(argv) > 2 else 0xe0
    f = '>' if e == 'be' else '<'
    D = DW.read(open(path, 'rb').read(), e)
    b = PB.block(D, e)
    if b is None: raise SystemExit('no player block')
    k, t, slots = b
    s = D.sections[k]
    d = bytes(s.data)
    it = dict(R.parse(bytes(s.reloc), e).internal)
    cnt = struct.unpack_from(f + 'i', d, t + 0xde4)[0]
    arr = it.get(t + 0xde8)
    print('block +0x%x count %d array %s' % (t, cnt, hex(arr) if arr is not None else None))
    if arr is None: return
    for j in range(cnt):
        rid = struct.unpack_from(f + 'I', d, arr + 8 * j)[0]
        x = it.get(arr + 8 * j + 4)
        print('== id %d X %s' % (rid, hex(x) if x is not None else None))
        if x is None: continue
        for o in range(0, ln, 16):
            row = []
            for q in range(o, min(o + 16, ln), 4):
                raw = d[x + q:x + q + 4]
                fl = struct.unpack(f + 'f', raw)[0]
                u = struct.unpack(f + 'I', raw)[0]
                tag = '*' if (x + q) in it else ''
                row.append('%s%s' % (('%.4g' % fl) if 1e-4 < abs(fl) < 1e7 else '0x%x' % u, tag))
            print('  +0x%03x  %s' % (o, '  '.join(row)))


if __name__ == '__main__':
    main(sys.argv[1:])
