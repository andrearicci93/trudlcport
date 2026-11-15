"""TruLink 0.4 prep (2026-11-15): sticky store entries of one owner in a full tru.exe minidump (read-only).

Store as TruMenu sticky.get (ENGINE.md 6.3): impl [0xa13f18], int store [impl+0] / bool [impl+4] / float [impl+8];
store +0 count, +8 entries (12 B {u32 owner, u16 key, u8 kind, pad, u32 watcher}), +0xc max; bool bits [store+0x14]
(size +0x18), int / float values [store+0x18] (size +0x1c).

Usage (from the repository root):
  ../bin/pyt -t 900 work/trulink04_1511/explore_sticky.py DUMP.dmp OWNER [KIND] [--data 0xADDR N]
"""
import os, struct, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import minidump_read as MR


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    M = MR.Minidump(argv[0])
    owner = int(argv[1], 0)
    kind = int(argv[2], 0) if len(argv) > 2 and not argv[2].startswith('--') else 0

    def u32(a):
        b = M.read(a, 4) if a else None
        return None if b is None else struct.unpack('<I', b)[0]

    impl = u32(0xa13f18)
    print('impl 0x%08x' % (impl or 0))
    for t, name in enumerate(('int', 'bool', 'float')):
        store = u32(impl + 4 * t)
        count, entries, mx = u32(store), u32(store + 8), u32(store + 0xc)
        print('%s store 0x%08x count %s max %s entries 0x%08x' % (name, store or 0, count, mx, entries or 0))
        if not entries or count is None or count > 0x1000: continue
        raw = M.read(entries, 12 * count)
        for i in range(count):
            o, k, kd = struct.unpack_from('<IHB', raw, 12 * i)
            if o == owner and kd == kind:
                if t == 1:
                    bits = u32(store + 0x14)
                    b = M.read(bits + (i >> 3), 1)[0]
                    v = (b >> (i & 7)) & 1
                else:
                    vals = u32(store + 0x18)
                    w = u32(vals + 4 * i)
                    v = struct.unpack('<f', struct.pack('<I', w))[0] if t == 2 else struct.unpack('<i', struct.pack('<I', w))[0]
                print('  %s index %d owner %d kind %d key %d value %s watcher 0x%08x' %
                      (name, i, o, kd, k, v, struct.unpack_from('<I', raw, 12 * i + 8)[0]))
    if '--data' in argv:
        a = int(argv[argv.index('--data') + 1], 16)
        n = int(argv[argv.index('--data') + 2])
        b = M.read(a, 4 * n)
        print('data 0x%08x: %s' % (a, ' '.join('%08x' % v for v in struct.unpack('<%dI' % n, b))))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
