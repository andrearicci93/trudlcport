"""TruLink 0.4 prep (2026-11-15): explore the live object structures in a full tru.exe minidump (read-only).

Prints the instance list with intro id / object name / unit / position / uber node, then for a few instances the
script object chain ([inst+0x60] -> +8 type -> members) to find the member layout in memory.

Usage (from the repository root):
  ../bin/pyt -t 900 work/trulink04_1511/explore_dump.py DUMP.dmp [--script N] [--inst 0xADDR]
"""
import os, struct, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import minidump_read as MR


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    M = MR.Minidump(argv[0])

    def u32(a):
        b = M.read(a, 4)
        return None if b is None else struct.unpack('<I', b)[0]

    def u16(a):
        b = M.read(a, 2)
        return None if b is None else struct.unpack('<H', b)[0]

    def f3(a):
        b = M.read(a, 12)
        return None if b is None else struct.unpack('<3f', b)

    def cstr(a, n=64):
        if not a: return None
        b = M.read(a, n)
        if b is None: return None
        z = b.find(b'\0')
        s = b[:z if z >= 0 else n]
        return s.decode('ascii', 'replace') if all(32 <= c < 127 for c in s) else None

    names = u32(0xdb94d0)
    ncount = u32(names) if names else 0

    def oname(oid):
        if not names or oid <= 0 or oid > ncount: return '?'
        return cstr(u32(names + oid * 8)) or '?'

    def unit_name(uid):
        for e in range(0xdbab40, 0xdbab40 + 32 * 0xd8, 0xd8):
            if u32(e) == uid and (M.read(e + 4, 1) or b'\0')[0] == 2:
                return cstr(e + 0xc, 128)
        return None

    def uber(inst):
        p = u32(inst + 0x2d0)
        if not p: return 0
        a = u32(p)
        if not a: return 0
        u = u32(a + 0x2ec)
        if not u or u < 0x10: return 0
        b = u - 0x10
        return b if u32(b + 0x70) == 0xf0012345 else 0

    def multibody(inst):
        p = u32(inst + 0x2d0)
        if not p: return 0
        a = u32(p)
        if not a: return 0
        u = u32(a + 0x2ec)
        if not u or u < 4: return 0
        x = u - 4
        return x if u32(x + 0x54) == 0xfea51b1e else 0

    def node_name(b, k):
        desc = u32(b + 0x78)
        if not desc: return ''
        cnt, nodes = u32(desc + 4), u32(desc + 8)
        if cnt is None or k is None or k >= cnt or not nodes: return ''
        return cstr(u32(nodes + 28 * k + 8)) or ''

    player = u32(0xe7f094)
    lara = f3(player + 0x20) if player else (0, 0, 0)
    print('player 0x%08x pos %s  object names table 0x%08x count %s' % (player or 0, lara, names or 0, ncount))
    inst = u32(0xd98d54)
    rows = []
    n = 0
    while inst and n < 4096:
        n += 1
        obj = u32(inst + 0x10) or 0
        oid = (u32(obj + 0x14) or 0) & 0xffff if obj else 0
        intro = u32(inst + 0x58)
        pos = f3(inst + 0x20) or (0, 0, 0)
        d = sum((pos[i] - lara[i]) ** 2 for i in range(3)) ** 0.5
        b = uber(inst)
        x = multibody(inst)
        node = ''
        if b:
            node = node_name(b, u32(b + 0x84))
        rows.append((d, inst, intro, oid, oname(oid), u32(inst + 0xe0), pos, b, x, node, u32(inst + 0x14), u32(inst + 0x60)))
        inst = u32(inst + 8)
    print('instances walked', n)
    rows.sort()
    for r in rows[:int(argv[argv.index('--near') + 1]) if '--near' in argv else 60]:
        d, inst, intro, oid, nm, unit, pos, b, x, node, fl, so = r
        print('%8.0f 0x%08x intro %10d obj %4d %-34s unit %4s %-22s pos %9.1f %9.1f %9.1f fl 0x%08x so 0x%08x%s%s'
              % (d, inst, intro, oid, nm, unit, unit_name(unit) or '?', pos[0], pos[1], pos[2], fl or 0, so or 0,
                 ' uber 0x%08x node %s' % (b, node) if b else '', ' X 0x%08x' % x if x else ''))
    want = int(argv[argv.index('--script') + 1]) if '--script' in argv else 6
    shown = 0
    for r in rows:
        so = r[11]
        if not so or shown >= want: continue
        shown += 1
        print('--- script of 0x%08x intro %d %s: so 0x%08x' % (r[1], r[2], r[4], so))
        raw = M.read(so, 0x20)
        print('   so words', [hex(v) for v in struct.unpack('<8I', raw)] if raw else None)
        t = u32(so + 8)
        if not t: continue
        raw = M.read(t, 0x48)
        print('   [so+8] 0x%08x words' % t, [hex(v) for v in struct.unpack('<18I', raw)] if raw else None)
        for off in (8, 0xc, 0x10):
            print('   [so+8]+0x%x as string: %s' % (off, cstr(u32(t + off) or 0)))
        mem = u32(t + 0x2c)
        cnt = u32(mem - 4) if mem else None
        print('   members ptr 0x%08x count %s' % (mem or 0, cnt))
        if mem and cnt is not None and cnt < 64:
            for k in range(cnt):
                e = M.read(mem + 20 * k, 20)
                if e is None: break
                tag, ut, uh, un, off, name, init = struct.unpack('<IHHIHHI', e)
                print('     m%d tag 0x%x user %d/%d union 0x%08x off %d name %d init 0x%08x init0 %s' %
                      (k, tag, ut, uh, un, off, name, init, hex(u32(init)) if init else '-'))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
