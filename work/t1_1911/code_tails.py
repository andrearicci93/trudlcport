"""T1 (b), read-only: which functions own the code arrays whose count word differs from the title update, and what
stands in the words between our count and the Xbox count (op bytes of the cut tail).

Usage (repo root): ../bin/pyt -t 900 work/t1_1911/code_tails.py DRM SID HEXOFF:XBOXCOUNT [...]
"""
import sys, os, struct
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
import drm_write as DW, drm_reloc as R, script_conv as SC


def main(argv):
    path, sid = argv[0], int(argv[1])
    D = DW.read(open(path, 'rb').read(), 'le')
    s = next(x for x in D.sections if x.type == 8 and x.id == sid)
    w = SC.Walk(s.data, R.parse(s.reloc, 'le'), 'le').run()
    funcs = [(t, n) for nm, t, n, sz in w.arrays if nm == 'funcs']
    owner = {}
    for t, n in funcs:
        for k in range(n):
            a = t + 28 * k
            c = w.it.get(a + 0x18)
            if c is not None: owner[c] = (k, a, struct.unpack_from('<H', s.data, w.it.get(a, a) + 8)[0] if a in w.it else None)
    for arg in argv[2:]:
        o, xn = arg.split(':'); o = int(o, 16); xn = int(xn)
        t = o + 4; cur = struct.unpack_from('<I', s.data, o)[0]
        k = owner.get(t)
        print('script %d +0x%x: code at +0x%x, count %d (Xbox %d), function %s' % (sid, o, t, cur, xn,
              'f%d (record +0x%x, prototype name sym %s)' % k if k else '?'))
        tail = [struct.unpack_from('<I', s.data, t + 4 * j)[0] for j in range(max(0, cur - 3), xn)]
        print('  words %d..%d: %s' % (max(0, cur - 3), xn - 1, ' '.join('%08x' % x for x in tail)))
        nxt = t + 4 * xn
        print('  word after the Xbox count (+0x%x): %s, labelled %s' % (nxt, '%08x' % struct.unpack_from('<I', s.data, nxt)[0]
              if nxt + 4 <= len(s.data) else '-', w.lab.get(nxt)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
