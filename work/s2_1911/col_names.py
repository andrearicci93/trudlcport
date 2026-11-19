"""Read-only: class names of MSVC RTTI CompleteObjectLocators (COL +0xc = TypeDescriptor, name at TD + 8) and, given a
vtable address instead (--vt), of the COL at vtable - 4 (S2 analysis 2026-11-19: which player state class a vtable
belongs to).

Usage (from the repository root):
  ../bin/pyt -t 120 work/s2_1911/col_names.py EXE [--vt] ADDR[,ADDR..]
"""
import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import pe_callers as PE


def off_of(secs, a):
    for _, sva, rptr, size, _ in secs:
        if sva <= a < sva + size: return rptr + a - sva
    return -1


def u32(exe, secs, a):
    o = off_of(secs, a)
    return struct.unpack_from('<I', exe, o)[0] if o >= 0 else None


def cstr(exe, secs, a):
    o = off_of(secs, a)
    if o < 0: return '?'
    e = exe.find(b'\0', o)
    return exe[o:e].decode('ascii', 'replace')


def main(argv):
    exe = open(argv[0], 'rb').read()
    base, secs = PE.sections(exe)
    vt = '--vt' in argv
    for s in argv[-1].split(','):
        a = int(s, 16)
        col = u32(exe, secs, a - 4) if vt else a
        td = u32(exe, secs, col + 0xc) if col else None
        print('0x%08x col 0x%08x td %s %s' % (a, col or 0, '0x%08x' % td if td else '-', cstr(exe, secs, td + 8) if td else '-'))


if __name__ == '__main__':
    main(sys.argv[1:])
