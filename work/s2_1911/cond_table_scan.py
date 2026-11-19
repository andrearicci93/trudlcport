"""Read-only: walk a PC state-chart condition / activity registration table of tru.exe ({u32 id, u32 group, u32
handler} for conditions, {u32 id, u32 handler} for activities; ends at id 0 or a non-code handler) and list for every
handler the memory displacements it uses inside a given range (S2 analysis 2026-11-19: which condition reads the
balance-beam helper at machine +0x358).

Usage (from the repository root):
  ../bin/pyt -t 300 work/s2_1911/cond_table_scan.py EXE TABLE_HEX cond|act LO_HEX HI_HEX [MAXBYTES]
"""
import sys, os, struct
import capstone
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import pe_callers as PE


def off_of(secs, a):
    for _, sva, rptr, size, _ in secs:
        if sva <= a < sva + size: return rptr + a - sva
    return -1


def main(argv):
    exe = open(argv[0], 'rb').read()
    base, secs = PE.sections(exe)
    tab, kind = int(argv[1], 16), argv[2]
    lo, hi = int(argv[3], 16), int(argv[4], 16)
    maxb = int(argv[5], 16) if len(argv) > 5 else 0x300
    stride = 12 if kind == 'cond' else 8
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    a = tab
    n = 0
    while n < 2000:
        o = off_of(secs, a)
        vals = struct.unpack_from('<%dI' % (stride // 4), exe, o)
        cid, h = vals[0], vals[-1]
        if cid == 0 or not (0x401000 <= h < 0x840000): break
        ho = off_of(secs, h)
        hits = []
        for ins in md.disasm(exe[ho:ho + maxb], h):
            if ins.mnemonic == 'int3': break
            for op in ins.operands:
                if op.type == capstone.x86.X86_OP_MEM and lo <= (op.mem.disp & 0xffffffff) < hi:
                    hits.append('%x:%s %s' % (ins.address, ins.mnemonic, ins.op_str))
        print('id %5d grp %s handler 0x%08x %s' % (cid, vals[1] if stride == 12 else '-', h,
              ('| ' + ' ; '.join(hits[:6])) if hits else ''))
        a += stride
        n += 1
    print('entries', n)


if __name__ == '__main__':
    main(sys.argv[1:])
