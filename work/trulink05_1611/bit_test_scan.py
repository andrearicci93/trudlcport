"""TruLink 0.5 (2026-11-16): every place in tru.exe that tests one bit of a dword field [reg + DISP] (read-only).

Linear capstone sweep over .text (as tools/exe_xref.py). A hit is
  - test/and/or/bt with a memory operand [reg + DISP] (or the byte holding the bit) and an immediate that has the bit;
  - a load mov/movzx reg, [reg + DISP] (or the byte) followed within the next 4 instructions by test/and/bt/shr on
    that register that can isolate the bit (test/and with the bit, test ah / bh.. form for bits 8..15, shr by the bit
    index, bt with the index).
Writes (or / and / mov to the field) are listed with --writes. Output: address, kind, instruction(s).

Usage (from the repository root):
  ../bin/pyt -t 900 work/trulink05_1611/bit_test_scan.py EXE DISP BIT [--writes]     (hex DISP, hex BIT mask)
"""
import os, sys
import capstone
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import exe_xref as XR

HIGH8 = {'ah': 'eax', 'bh': 'ebx', 'ch': 'ecx', 'dh': 'edx'}
LOW8 = {'al': 'eax', 'bl': 'ebx', 'cl': 'ecx', 'dl': 'edx'}


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    path, disp, bit = argv[0], int(argv[1], 16), int(argv[2], 16)
    show_writes = '--writes' in argv
    index = bit.bit_length() - 1
    byte_disp = disp + index // 8
    byte_bit = 1 << (index % 8)
    code, va = XR.text(path)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    md.skipdata = True
    ins_list = [i for i in md.disasm(code, va) if i.id != 0]
    hits = 0
    for n, ins in enumerate(ins_list):
        mems = [op for op in ins.operands if op.type == capstone.x86.X86_OP_MEM and op.mem.base != 0]
        if not mems:
            continue
        m = mems[0]
        d = m.mem.disp
        if d not in (disp, byte_disp):
            continue
        imms = [op.imm & 0xffffffff for op in ins.operands if op.type == capstone.x86.X86_OP_IMM]
        want = bit if d == disp else byte_bit
        mn = ins.mnemonic
        if mn in ('test', 'bt') and imms and (imms[0] & want if mn == 'test' else imms[0] == (index if d == disp else index % 8)):
            print('%08x  test   %s %s' % (ins.address, mn, ins.op_str)); hits += 1
            continue
        if mn in ('and', 'or', 'mov', 'xor') and XR.writes(m):
            if show_writes and (not imms or imms[0] & want or (mn == 'and' and not imms[0] & want)):
                print('%08x  write  %s %s' % (ins.address, mn, ins.op_str))
            continue
        if mn in ('mov', 'movzx', 'movsx') and ins.operands[0].type == capstone.x86.X86_OP_REG:
            reg = ins.reg_name(ins.operands[0].reg)
            for nxt in ins_list[n + 1:n + 5]:
                ops = nxt.op_str.replace(' ', '').split(',')
                if not ops or not ops[0]:
                    continue
                r0 = ops[0]
                same = r0 == reg or HIGH8.get(r0) == reg or LOW8.get(r0) == reg or (reg.startswith('e') and r0 == reg[1:])
                if not same:
                    if r0 == reg:
                        break
                    continue
                try:
                    imm = int(ops[1], 0) if len(ops) > 1 else None
                except ValueError:
                    imm = None
                found = False
                if nxt.mnemonic in ('test', 'and') and imm is not None:
                    shift = 8 if r0 in HIGH8 else 0
                    mask = (bit if d == disp else byte_bit) >> shift if r0 in HIGH8 else (bit if d == disp else byte_bit)
                    found = bool(imm & mask) if r0 not in HIGH8 else bool((imm << 8) & (bit if d == disp else byte_bit << 0))
                elif nxt.mnemonic == 'shr' and imm == (index if d == disp else index % 8):
                    found = True
                elif nxt.mnemonic == 'bt' and imm == (index if d == disp else index % 8):
                    found = True
                if found:
                    print('%08x  load   %s %s  ->  %08x %s %s' % (ins.address, mn, ins.op_str, nxt.address, nxt.mnemonic,
                                                             nxt.op_str)); hits += 1
                    break
    print('# %d test site(s) of bit 0x%x at +0x%x' % (hits, bit, disp))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
