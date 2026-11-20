"""A2 (2026-11-20): slots of Lara's machine-1 state table in tru.exe (read only). Table 0x8b0a50, entries of 0x1c
bytes {u32 state id, 6 handler slots} (slot 0 enter, 1 re-enter, 2 exit, 3 tick, 4 / 5 messages; ENGINE section 12).

Usage (from the repository root):
  ../bin/pyt -t 60 work/a2_2011/a2_state_slots.py EXE ID[,ID..] [TABLE_HEX COUNT]
"""
import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import pe_callers as PE


def va_off(secs, va):
    for sec in secs:
        if sec[1] <= va < sec[1] + sec[3]:
            return sec[2] + va - sec[1]
    return -1


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    exe = open(argv[0], 'rb').read()
    base, secs = PE.sections(exe)
    want = set(int(x) for x in argv[1].split(','))
    tab = int(argv[2], 16) if len(argv) > 2 else 0x8b0a50
    cnt = int(argv[3]) if len(argv) > 3 else 400
    o = va_off(secs, tab)
    for k in range(cnt):
        w = struct.unpack_from('<7I', exe, o + 0x1c * k)
        if w[0] in want:
            print('entry %d at 0x%08x: state %d slots %s' % (k, tab + 0x1c * k, w[0],
                  ' '.join('0x%08x' % x for x in w[1:])))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
