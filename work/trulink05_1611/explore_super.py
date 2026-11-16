"""TruLink 0.5 prep (2026-11-16): the script class chain of instances in a full tru.exe minidump (read-only).

  so = [inst+0x60]; t = [so+8] runtime ScriptType (vtable 0x84e4d4); root = [t+8]; class id = u16 [root+8];
  super = [root+0x18] = the base class's runtime ScriptType (0x5749e0 IsA walks t = [root+0x18]); name [root+0x10];
  members [root+0x2c] (count at ptr-4, 20 B: tag, user u16 +4, union +8, offset u16 +0xc, name u16 +0xe, init +0x10)

For each instance (intro id or 0x address) prints every class of the chain with its members and their raw data
words (data = [so+0xc] + offset).

Usage (from the repository root):
  ../bin/pyt -t 900 work/trulink05_1611/explore_super.py DUMP.dmp ID_OR_ADDR ...
"""
import os, struct, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import minidump_read as MR

INSTANCE_LIST = 0x00d98d54
SCRIPT_TYPE_VT = 0x0084e4d4


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    M = MR.Minidump(argv[0])

    def u32(a):
        b = M.read(a, 4) if a else None
        return None if b is None else struct.unpack('<I', b)[0]

    def u16(a):
        b = M.read(a, 2) if a else None
        return None if b is None else struct.unpack('<H', b)[0]

    def cstr(a):
        b = M.read(a, 48) if a else None
        if not b:
            return '?'
        s = b.split(b'\0')[0]
        return s.decode('ascii', 'replace') if s and all(32 <= c < 127 for c in s) else '?'

    insts = []
    p = u32(INSTANCE_LIST)
    while p and len(insts) < 4096:
        insts.append(p)
        p = u32(p + 8)
    by_intro = {u32(x + 0x58): x for x in insts}
    for s in argv[1:]:
        x = int(s, 16) if s.lower().startswith('0x') else by_intro.get(int(s))
        if not x:
            print('# %s: not in the instance list' % s)
            continue
        so = u32(x + 0x60)
        print('# inst 0x%08x intro %d script object 0x%08x' % (x, u32(x + 0x58), so or 0))
        if not so:
            continue
        data = u32(so + 0xc)
        t = u32(so + 8)
        depth = 0
        while t and depth < 12:
            vt = u32(t)
            root = u32(t + 8)
            if vt != SCRIPT_TYPE_VT or not root:
                print('  type 0x%08x: vtable 0x%08x root 0x%08x - stop' % (t, vt or 0, root or 0))
                break
            mptr = u32(root + 0x2c)
            count = u32(mptr - 4) if mptr else 0
            print('  depth %d type 0x%08x root 0x%08x class id %d name "%s" self +0x14 %s super +0x18 0x%08x '
                  'members %d data size? +0x1c %s +0x20 %s' % (
                      depth, t, root, u16(root + 8), cstr(u32(root + 0x10)), u32(root + 0x14), u32(root + 0x18) or 0,
                      count or 0, u32(root + 0x1c), u32(root + 0x20)))
            for k in range(min(count or 0, 64)):
                e = mptr + 20 * k
                tag, user, uni, off, name, init = u32(e), u16(e + 4), u32(e + 8), u16(e + 0xc), u16(e + 0xe), u32(e + 0x10)
                tname = ''
                if (tag & 0xf) in (0xa, 0xb) and uni:
                    st = u32(uni) if tag & 0x80 else uni
                    r = u32(st + 8) if st and u32(st) == SCRIPT_TYPE_VT else None
                    tname = cstr(u32(r + 0x10)) if r else 'type%d' % user
                else:
                    tname = 'bt%d' % (tag & 0xf)
                raw = u32(data + off) if data is not None else None
                print('    m%d +%d %s tag 0x%x user %d name sym %d init 0x%08x data 0x%08x' % (
                    k, off, tname, tag, user, name, init or 0, raw if raw is not None else 0))
            t = u32(root + 0x18)
            depth += 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
