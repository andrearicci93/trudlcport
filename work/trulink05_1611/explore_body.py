"""TruLink 0.5 prep (2026-11-16): the physics body at instance +0x274 in a full tru.exe minidump (read-only).

For each given instance (address or intro id): position +0x20 / rotation +0x30, the body pointer +0x274 and the body's
first LEN bytes as dwords (hex, float), marking every float that equals one of the instance's position components
(a hint where the body keeps its pose). Optional --scan: every instance of the list with a body (pointer + offsets).

Usage (from the repository root):
  ../bin/pyt -t 900 work/trulink05_1611/explore_body.py DUMP.dmp [--len 0x200] [--scan] ID_OR_ADDR ...
"""
import os, struct, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import minidump_read as MR

INSTANCE_LIST = 0x00d98d54


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    M = MR.Minidump(argv[0])
    length = 0x200
    scan = False
    ids = []
    i = 1
    while i < len(argv):
        if argv[i] == '--len':
            length = int(argv[i + 1], 0); i += 2; continue
        if argv[i] == '--scan':
            scan = True; i += 1; continue
        ids.append(argv[i]); i += 1

    def u32(a):
        b = M.read(a, 4)
        return None if b is None else struct.unpack('<I', b)[0]

    def f3(a):
        b = M.read(a, 12)
        return None if b is None else struct.unpack('<3f', b)

    insts = []
    p = u32(INSTANCE_LIST)
    while p and len(insts) < 4096:
        insts.append(p)
        p = u32(p + 8)
    by_intro = {u32(x + 0x58): x for x in insts}
    if scan:
        print('# instances with a body +0x274 (%d instances walked)' % len(insts))
        for x in insts:
            b = u32(x + 0x274)
            if b:
                print('inst 0x%08x intro %d body 0x%08x pos %s' % (x, u32(x + 0x58), b,
                                                                     ' '.join('%.2f' % v for v in f3(x + 0x20))))
    for s in ids:
        x = int(s, 16) if s.lower().startswith('0x') else by_intro.get(int(s))
        if not x:
            print('# %s: not in the instance list' % s)
            continue
        pos, rot = f3(x + 0x20), f3(x + 0x30)
        body = u32(x + 0x274)
        print('# inst 0x%08x intro %d pos %s rot %s body +0x274 0x%08x' % (
            x, u32(x + 0x58), ' '.join('%.3f' % v for v in pos), ' '.join('%.4f' % v for v in rot), body or 0))
        if not body:
            continue
        raw = M.read(body, length)
        if raw is None:
            print('#   body not readable')
            continue
        for o in range(0, length, 4):
            w = struct.unpack_from('<I', raw, o)[0]
            f = struct.unpack_from('<f', raw, o)[0]
            mark = ''
            for k, v in enumerate(pos):
                if abs(f - v) < 0.05:
                    mark += ' == pos[%d]' % k
            ff = ('%.5g' % f) if abs(f) < 1e7 and (f == 0 or abs(f) > 1e-6) else '-'
            print('  +0x%03x 0x%08x %12s%s' % (o, w, ff, mark))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
