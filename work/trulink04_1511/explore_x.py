"""TruLink 0.4 prep (2026-11-15): one multibody object X in a full tru.exe minidump (read-only).

  X = [[inst+0x2d0]]+0x2ec - 4 (magic 0xFEA51B1E at X+0x54, vtable 0x847f70 / 0x85d55c), X+0x58 instance,
  X+0x6c link handles {inst, stamp = [inst+0x44]} (count X+0x70), X+0x74 joint list sentinel (node +8 record, +0x1c J);
  command table of [[X+0x58]+0x50]: +0x10 count, +0x14 entries 12 B {?, n +4, records +8}, record 12 B {link, kind, value}

Usage (from the repository root):
  ../bin/pyt -t 900 work/trulink04_1511/explore_x.py DUMP.dmp 0xINSTANCE
"""
import os, struct, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import minidump_read as MR


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    M = MR.Minidump(argv[0])

    def u32(a):
        b = M.read(a, 4) if a else None
        return None if b is None else struct.unpack('<I', b)[0]

    def f(a):
        b = M.read(a, 4) if a else None
        return None if b is None else struct.unpack('<f', b)[0]

    def cstr(a, n=64):
        b = M.read(a, n) if a else None
        if b is None: return None
        z = b.find(b'\0')
        s = b[:z if z >= 0 else n]
        return s.decode('ascii', 'replace') if all(32 <= c < 127 for c in s) else None

    def uber(inst):
        p = u32(inst + 0x2d0); a = u32(p) if p else None; u = u32(a + 0x2ec) if a else None
        if not u or u < 0x10: return 0
        return u - 0x10 if u32(u - 0x10 + 0x70) == 0xf0012345 else 0

    def node_name(b, k):
        desc = u32(b + 0x78); cnt = u32(desc + 4) if desc else None; nodes = u32(desc + 8) if desc else None
        if cnt is None or k is None or k >= cnt: return '?'
        return cstr(u32(nodes + 28 * k + 8)) or '?'

    inst = int(argv[1], 16)
    p = u32(inst + 0x2d0); a = u32(p) if p else None; u = u32(a + 0x2ec) if a else None
    x = u - 4 if u else 0
    print('inst 0x%08x X 0x%08x vt 0x%08x magic 0x%08x X+0x58 0x%08x' % (inst, x, u32(x) or 0, u32(x + 0x54) or 0, u32(x + 0x58) or 0))
    n = u32(x + 0x70); h = u32(x + 0x6c)
    print('links %s at 0x%08x' % (n, h or 0))
    for i in range(min(n or 0, 64)):
        li, st = u32(h + 8 * i), u32(h + 8 * i + 4)
        ok = li and u32(li + 0x44) == st
        b = uber(li) if ok else 0
        print('  link %d inst 0x%08x stamp %s ok %s intro %s uber 0x%08x node %s b+0x7c 0x%08x' %
              (i, li or 0, st, bool(ok), u32(li + 0x58) if ok else '-', b, node_name(b, u32(b + 0x84)) if b else '-',
               u32(b + 0x7c) or 0 if b else 0))
    data = u32(u32(x + 0x58) + 0x50)
    cn, ce = u32(data + 0x10), u32(data + 0x14)
    print('object data 0x%08x commands %s at 0x%08x' % (data or 0, cn, ce or 0))
    for c in range(min(cn or 0, 32)):
        e0, rn, rp = u32(ce + 12 * c), u32(ce + 12 * c + 4), u32(ce + 12 * c + 8)
        recs = []
        for r in range(min(rn or 0, 16)):
            recs.append('{link %s kind %s value %s}' % (u32(rp + 12 * r), u32(rp + 12 * r + 4), u32(rp + 12 * r + 8)))
        print('  cmd %d: +0 0x%08x n %s %s' % (c, e0 or 0, rn, ' '.join(recs)))
    s = u32(x + 0x74)
    node = u32(s) if s else None
    i = 0
    while node and node != s and i < 64:
        rec, j = u32(node + 8), u32(node + 0x1c)
        t = (M.read(j + 0x178, 1) or b'\xff')[0] if j else None
        fl = u32(j + 0x174) if j else None
        print('  joint %d node 0x%08x rec 0x%08x rec type %s A %s B %s J 0x%08x phys %s lim [%s, %s] flags %s mvel %s mforce %s' %
              (i, node, rec or 0, (M.read(rec, 1) or b'?')[0] if rec else None, u32(rec + 4) if rec else None,
               u32(rec + 8) if rec else None, j or 0, t, f(j + 0xd8) if j else None, f(j + 0xdc) if j else None,
               hex(fl) if fl is not None else None, f(j + 0x108) if j else None, f(j + 0x10c) if j else None))
        node = u32(node); i += 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
