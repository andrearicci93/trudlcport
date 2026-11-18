"""Read-only: print the fall damage thresholds of the player data block (`[0xfad764]` +0x4c / +0x50 / +0x54, read by
0x702e90) and nearby words for the five base player pairs (Xbox BE / PC LE), using tools/player_block_fix.py's
extraction (R2 fall damage, 2026-11-18).

Usage (from the repository root):
  ../bin/pyt -t 900 work/r2_1811/fall_tune.py [FROM TO]     word offsets in hex (default 0x40 0x60)
  ../bin/pyt -t 900 work/r2_1811/fall_tune.py --drm DRM ENDIAN FROM TO   one DRM (be / le) with a player block
"""
import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import player_block_fix as PB
import drm_write as DW


def one(path, e, lo, hi):
    D = DW.read(open(path, 'rb').read(), e)
    w = PB.words(D, e)
    if w is None: raise SystemExit('no player block in %s' % path)
    k, t, ws, slots = w
    f = '>f' if e == 'be' else '<f'
    print('== %s section %d block +0x%x' % (os.path.basename(path), k, t))
    for o in range(lo, hi, 4):
        print('  +0x%03x  %-14r raw %s' % (o, round(struct.unpack(f, ws[o // 4])[0], 4), ws[o // 4].hex()))


def main(argv):
    if argv and argv[0] == '--drm':
        return one(argv[1], argv[2], int(argv[3], 16), int(argv[4], 16))
    lo = int(argv[0], 16) if argv else 0x40
    hi = int(argv[1], 16) if len(argv) > 1 else 0x60
    for name, xw, pw, slots, pmap in PB.base_pairs():
        print('==', name)
        for o in range(lo, hi, 4):
            x = struct.unpack('>f', xw[o // 4])[0]; p = struct.unpack('<f', pw[o // 4])[0]
            print('  +0x%03x  xbox %-14r pc %-14r  pc raw %s' % (o, round(x, 4), round(p, 4), pw[o // 4].hex()))


if __name__ == '__main__':
    main(sys.argv[1:])
