"""R8 helper (read-only, 2026-11-18): find script code words (opcode << 24 | operand) in the type-8 sections of the
PC base units of one level group, e.g. op14 1824 = 'member +1824 of the object on the stack' (the objective flags of
globals sub +12). Prints unit, script id, data offset and the two words before the match.
Output is game data: write it to <workspace>/local_results/, never into the repository.

Usage (from the repository root):
  ../bin/pyt -t 900 work/r8_1811/code_word_find.py GROUP OP:OPERAND[,OP:OPERAND...]
  GROUP = l3 (unit name prefix group of tools/puzzle_switch_scan.unit_group), OP hex (14), OPERAND decimal (1824)
"""
import sys, os, struct
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
import puzzle_switch_scan as PS


def main(argv):
    if len(argv) < 2:
        print(__doc__); return 2
    grp = argv[0]
    want = {}
    for t in argv[1].split(','):
        op, val = t.split(':')
        want[(int(op, 16) << 24) | int(val)] = t
    S = PS.Source('pc', None)
    hits = 0
    for name, g in S.units:
        if g != grp: continue
        secs = S.drm(name) or []
        for s in secs:
            if s['type'] != 8 or not s['data']: continue
            d = bytes(s['data'])
            for o in range(0, len(d) - 3, 4):
                w = struct.unpack_from('<I', d, o)[0]
                if w in want:
                    prev = [struct.unpack_from('<I', d, o - 4 * k)[0] for k in (2, 1) if o - 4 * k >= 0]
                    print('%-28s script %6d +%#06x %s prev %s' % (name, s['id'], o, want[w], ' '.join('%08x' % p for p in prev)))
                    hits += 1
    print('# %d hits' % hits)
    return 0 if hits else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
