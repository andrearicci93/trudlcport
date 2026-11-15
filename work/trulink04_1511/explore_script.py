"""TruLink 0.4 prep (2026-11-15): script object chain of one instance in a full tru.exe minidump (read-only).

  so = [inst+0x60]; t = [so+8] (vtable 0x84e4d4 object); root = [t+8]? -> +0x14 self id, +0x18 super id, +0x2c
  members (20 B: tag, user u16, union, off u16 +0xc, name u16 +0xe, init +0x10), count at ptr-4

Usage (from the repository root):
  ../bin/pyt -t 900 work/trulink04_1511/explore_script.py DUMP.dmp 0xINSTANCE [0xINSTANCE ...]
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

    def words(a, n):
        b = M.read(a, 4 * n) if a else None
        return ' '.join('%08x' % v for v in struct.unpack('<%dI' % n, b)) if b else '-'

    def cstr(a, n=64):
        b = M.read(a, n) if a else None
        if b is None: return None
        z = b.find(b'\0')
        s = b[:z if z >= 0 else n]
        return s.decode('ascii', 'replace') if all(32 <= c < 127 for c in s) else None

    for arg in argv[1:]:
        inst = int(arg, 16)
        so = u32(inst + 0x60)
        print('=== inst 0x%08x so 0x%08x' % (inst, so or 0))
        print(' so   ', words(so, 12))
        t = u32(so + 8)
        print(' t    0x%08x: %s' % (t or 0, words(t, 16)))
        root = u32(t + 8)
        print(' root 0x%08x: %s' % (root or 0, words(root, 20)))
        for off in (8, 0xc, 0x10):
            print('  root+0x%x -> %s' % (off, cstr(u32(root + off)) if root else None))
        mem = u32(root + 0x2c) if root else None
        cnt = u32(mem - 4) if mem else None
        print(' members 0x%08x count %s' % (mem or 0, cnt))
        if mem and cnt is not None and cnt <= 200:
            for k in range(cnt):
                e = M.read(mem + 20 * k, 20)
                if e is None: break
                tag, ut, uh, un, off, name, init = struct.unpack('<IHHIHHI', e)
                i0 = u32(init) if init else None
                sub = u32(un) if un else None
                print('  m%-2d tag 0x%04x bt %2d user %5d/%d union 0x%08x off +%-4d name %5d init 0x%08x: %s | union: %s' %
                      (k, tag, tag & 0xf, ut, uh, un, off, name, init, words(init, 4), words(un, 6)))
                if '--types' in argv and un:
                    # bt 10: tag bit 7 -> union = Compound {ScriptType*, DataType* sub}, else union = ScriptType*;
                    # ScriptType (vtable 0x84e4d4) +8 = stream root: +0xc native package, +0x10 native name
                    st = u32(un) if tag & 0x80 else un
                    rt = u32(st + 8) if st else None
                    vt = u32(st) if st else None
                    print('      type 0x%08x vt %s root 0x%08x pkg %s native %s self %s' %
                          (st or 0, '%08x' % vt if vt is not None else '-', rt or 0,
                           cstr(u32(rt + 0xc)) if rt else None, cstr(u32(rt + 0x10)) if rt else None,
                           words(rt + 0x14, 2) if rt else '-'))
        data = u32(so + 0xc)
        print(' data 0x%08x: %s' % (data or 0, words(data, 16)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
