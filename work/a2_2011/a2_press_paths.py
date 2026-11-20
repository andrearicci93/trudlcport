"""A2 (2026-11-20): which records a jump press leads to from a given chart record (read only).

For the record and every parent (+6, recursive, as the selection 0x787570 walks them) the transitions that test the
jump action - condition 101 (action 52 via 0x7607c0, value 3 = pressed this frame) or condition 152 (action-set bit
0x10, value = action 52) - are listed in table order with their kind list and conditions; for each target the state
ids and the jump ids it sets: activity 541 (0x21d, handler 0x766ec0 -> slot A T+0xb00) and 546 (0x222 -> slot B
T+0xc90), own value or the nearest parent's, followed one level further when the target itself sets none.

Usage (from the repository root):
  ../bin/pyt -t 300 work/a2_2011/a2_press_paths.py DRM ENDIAN SID REC[,REC..]
"""
import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import chart_state_path as CP


def parent_of(C, k):
    hdr = C.state(k)[1]
    p = hdr[3] - 0x10000 if hdr[3] & 0x8000 else hdr[3]
    if p < 0:
        return None
    ks = CP.targets(C, p)
    return ks[0] if ks else None


def jump_ids(C, k):
    """(slot A, slot B, record that set it) - own activity or the nearest parent's"""
    a = b = None
    src = []
    seen = set()
    while k is not None and k not in seen:
        seen.add(k)
        for i, ty, v in C.state(k)[2]:
            val = struct.unpack(C.f + 'I', v)[0]
            if i == 541 and a is None:
                a = val; src.append('A from #%d' % k)
            if i == 546 and b is None:
                b = val; src.append('B from #%d' % k)
        k = parent_of(C, k)
    return a, b, src


def is_press(conds):
    for ky, i, v, fl in conds:
        if i == 101 and v == 3 and not (fl & 1):
            return True
        if i == 152 and v == 52 and not (fl & 1):
            return True
    return False


def chain_sids(C, k):
    out = []
    seen = set()
    while k is not None and k not in seen:
        seen.add(k)
        out.append('#%d%s' % (k, C.state(k)[3]))
        k = parent_of(C, k)
    return ' <- '.join(out)


def main(argv):
    if len(argv) < 4:
        print(__doc__)
        return 2
    C = CP.Chart(argv[0], argv[1], int(argv[2]))
    for rs in argv[3].split(','):
        k0 = CP.targets(C, int(rs))[0]
        print('== record #%d: %s' % (k0, chain_sids(C, k0)))
        k = k0
        seen = set()
        while k is not None and k not in seen:
            seen.add(k)
            for ti in C.state(k)[4]:
                if ti >= len(C.tlist):
                    continue
                a, tg, w1, cnt, w3, conds = C.trans(ti)
                if not is_press(conds):
                    continue
                ks = CP.targets(C, tg)
                tk = ks[0] if ks else None
                kinds = C.kinds(ti) if w1 else []
                line = '  in #%d: slot %d -> %d %s%s' % (k, ti, tg, ('kinds %s ' % kinds) if kinds else '',
                                                        CP.fmt_conds(conds))
                if tk is not None:
                    ja, jb, src = jump_ids(C, tk)
                    line += ' | target sids %s, jump A %s B %s (%s)' % (C.state(tk)[3], ja, jb, ', '.join(src))
                print(line)
            k = parent_of(C, k)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
