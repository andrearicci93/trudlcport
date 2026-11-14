"""Read-only (doppel_1411, 2026-11-14): disassemble N instructions of a PE (x86) at VA.
Usage (from trudlcport): ../bin/pyt -t 120 work/doppel_1411/dis.py EXE VA[,VA..] [N]"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import pe_callers as PE
import capstone


def main(a):
    exe = open(a[0], 'rb').read()
    base, secs = PE.sections(exe)
    n = int(a[2]) if len(a) > 2 else 40
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    for va in (int(x, 16) for x in a[1].split(',')):
        off = -1
        for _, sva, rptr, size, _ in secs:
            if sva <= va < sva + size: off = rptr + va - sva
        if off < 0: print('0x%08x not in a section' % va); continue
        print('== 0x%08x' % va)
        k = 0
        for ins in md.disasm(exe[off:off + 16 * n], va):
            print('  0x%08x  %-24s %s %s' % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
            k += 1
            if k >= n: break
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
