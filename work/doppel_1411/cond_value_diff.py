"""Read-only (doppel_1411, 2026-11-14): compare the condition records of every transition of a player state chart DTP
between the Xbox original (be) and converted PC files (le), offset by offset (the converter keeps the DTP layout).

Usage (from the repository root):
  ../bin/pyt -t 900 work/doppel_1411/cond_value_diff.py XBOX.drm SID PC.drm [PC2.drm ..] [--cond 2101,150]
Prints: per PC file, every transition whose condition list differs from the Xbox one (by offset), and with --cond
every transition (Xbox + PC side by side) that holds one of the given condition ids.
"""
import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import drm_write as DW, drm_reloc as R


def load(path, e, sid):
    D = DW.read(open(path, 'rb').read(), e)
    for s in D.sections:
        if s.id == sid and s.type == 7:
            return s
    raise SystemExit('DTP %d not in %s' % (sid, path))


def transitions(s, e):
    """{offset: (target, w1, count, w3, cond_offset, [(key, id, value, flags)])}"""
    f = '>' if e == 'be' else '<'
    d = bytes(s.data); it = dict(R.parse(bytes(s.reloc), e).internal)
    t = sorted(set(it.values()) | {0}); out = {}
    for k, a in enumerate(t):
        end = t[k + 1] if k + 1 < len(t) else len(d)
        if end - a != 0x14 or (a + 8) not in it or (a + 0xc) not in it: continue
        target, w1, cnt, w3 = struct.unpack_from(f + '4H', d, a)
        c0 = it[a + 8]; conds = []
        for j in range(min(cnt, 24)):
            if c0 + 8 * j + 8 > len(d): break
            ky, i, v = struct.unpack_from(f + '3H', d, c0 + 8 * j); fl = d[c0 + 8 * j + 6]
            conds.append((ky, i, v, fl))
        out[a] = (target, w1, cnt, w3, c0, conds)
    return out


def fmt(c): return ' '.join('{%d,%d,%d%s}' % (x[0], x[1], x[2], ',NOT' if x[3] & 1 else '') for x in c)


def main(argv):
    cids = None
    if '--cond' in argv:
        k = argv.index('--cond'); cids = set(int(x) for x in argv[k + 1].split(',')); del argv[k:k + 2]
    xb, sid, pcs = argv[0], int(argv[1]), argv[2:]
    X = transitions(load(xb, 'be', sid), 'be')
    print('Xbox %s DTP %d: %d transitions' % (xb, sid, len(X)))
    for p in pcs:
        P = transitions(load(p, 'le', sid), 'le')
        print('\n== %s: %d transitions, %d at the same offsets' % (os.path.basename(p), len(P), len(set(X) & set(P))))
        nd = 0
        for a in sorted(set(X) & set(P)):
            x, y = X[a], P[a]
            if (x[0], x[2], x[5]) != (y[0], y[2], y[5]):
                nd += 1
                print('  DIFF +0x%05x  X -> %5d %s' % (a, x[0], fmt(x[5])))
                print('               P -> %5d %s' % (y[0], fmt(y[5])))
        print('  transitions differing: %d' % nd)
        if cids:
            print('  -- transitions with condition ids %s --' % sorted(cids))
            for a in sorted(set(X) & set(P)):
                x, y = X[a], P[a]
                if any(c[1] in cids for c in x[5]) or any(c[1] in cids for c in y[5]):
                    same = 'same' if x[5] == y[5] else 'DIFF'
                    print('  +0x%05x %s  X -> %5d %s | P -> %5d %s' % (a, same, x[0], fmt(x[5]), y[0], fmt(y[5])))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
