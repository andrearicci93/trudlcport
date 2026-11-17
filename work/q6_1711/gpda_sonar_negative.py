r"""Q6 negative test of gate 13 (tools/gpda_dlc2_sonar.gate): a built entry-variant g_pda, mutated in memory - each
mutation must be reported; the unmutated file must pass. Read-only (nothing written).

Usage (from trudlcport):
  ../bin/pyt -t 300 work/q6_1711/gpda_sonar_negative.py ENTRY_G_PDA
Exit 0 = every case as expected.
"""
import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import drm_write as DW, drm_reloc as R
import gpda_dlc2_sonar as V


def run(d, rl):
    return V.gate(bytes(d), R.parse(rl, 'le'))


def main(a):
    D = DW.read(open(a[0], 'rb').read(), 'le')
    s = next(x for x in D.sections if x.type == 8 and x.id == V.SID)
    base = bytearray(s.data)
    mode, ex, probs, info = run(base, s.reloc)
    cases = [('unmutated', mode == 'entry' and not probs and len(ex) == 4, '%s %d problems' % (mode, len(probs)))]
    b1 = int(info['B1']['block'], 16); b3 = int(info['B3']['block'], 16)

    def mut(name, fn, want):
        d = bytearray(base); fn(d)
        m, e, p, i = run(d, s.reloc)
        ok = bool(p) if want == 'problem' else (m == want and not p)
        cases.append((name, ok, '%s, %d problems %s' % (m, len(p), p[:2])))
    # a block word other than planned (member +340 -> +328, the row-5 label)
    mut('B1 label member', lambda d: struct.pack_into('<I', d, b1 + 8, V.op(0x0f, 328)), 'problem')
    # a jump of B3 retargeted by one word (no longer an op00 marker of f10 / the planned word)
    mut('B3 jump +1 word', lambda d: struct.pack_into('<I', d, b3 + 0x7c, struct.unpack_from('<I', d, b3 + 0x7c)[0] + 1), 'problem')
    # one site back to its op00 marker (incomplete variant)
    mut('B2 site restored', lambda d: struct.pack_into('<I', d, 0x5bd0, V.op(0, 268)), 'problem')
    # a row-4 y word left at row 8
    mut('W1 y row 8', lambda d: struct.pack_into('<I', d, 0x8540, 0x40600000), 'problem')
    # read-with-store shape: the store opcode in B3's m1024 statement replaced by a byte store (op2e)
    mut('B3 op2f -> op2e', lambda d: struct.pack_into('<I', d, b3 + 0x28, V.op(0x2e)), 'problem')
    bad = 0
    for name, ok, why in cases:
        print('%-18s %s  %s' % (name, 'ok  ' if ok else 'FAIL', why)); bad += not ok
    print('%d / %d as expected' % (len(cases) - bad, len(cases)))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
