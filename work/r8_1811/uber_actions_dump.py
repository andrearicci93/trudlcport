"""R8 helper (read-only, 2026-11-18): raw dump of the uber block of one PC base object - per DESC / node the action
records (0x10 B) and the transitions (0x20 B) word by word, and for every word that is an internal pointer the 0x30
bytes it points at (u32 + float view). For reading joint / range / motor arguments that ObjInfo does not decode.
Output is game data: write it to <workspace>/local_results/, never into the repository.

Usage (from the repository root):
  ../bin/pyt -t 900 work/r8_1811/uber_actions_dump.py OBJECT_NAME
"""
import sys, os, struct
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
import drm_reloc as R
import menu_dlc_probe as P
import puzzle_switch_scan as PS


def words(d, it, o, n, E):
    out = []
    for k in range(n):
        p = o + 4 * k
        if p + 4 > len(d): break
        v = struct.unpack_from(E + 'I', d, p)[0]
        f = struct.unpack_from(E + 'f', d, p)[0]
        tag = ('->%#x' % it[p]) if p in it else ''
        fs = ('%.4g' % f) if v and 1e-6 < abs(f) < 1e9 else ''
        out.append('%08x%s%s' % (v, tag, ('(' + fs + ')') if fs else ''))
    return ' '.join(out)


def deref(d, it, o, n, E, ind):
    for k in range(n):
        p = o + 4 * k
        if p in it:
            print('%s  [+%#x -> %#x] %s' % (ind, 4 * k, it[p], words(d, it, it[p], 12, E)))


def main(argv):
    if not argv:
        print(__doc__); return 2
    S = PS.Source('pc', None)
    secs = S.drm(argv[0])
    if not secs:
        print('object %s not found' % argv[0]); return 1
    E = '>' if S.e == 'be' else '<'
    for s in secs:
        if s['type'] != 7 or not s['data']: continue
        d = bytes(s['data']); it = dict(R.parse(bytes(s['reloc']), S.e).internal)
        u = lambda o: struct.unpack_from(E + 'I', d, o)[0] if 0 <= o <= len(d) - 4 else None
        U = it.get(0xc8)
        if U is None or u(U + 4) not in (PS.UBER_MAGIC, PS.UBER_MAGIC_BE): continue
        print('# %s DTP %d uber block %#x: %s' % (argv[0], s['id'], U, words(d, it, U, 8, E)))
        nd = u(U + 8) or 0; D0 = it.get(U + 0xc)
        for m in range(nd):
            D = D0 + 0x54 * m
            print('DESC %d @%#x: %s' % (m, D, words(d, it, D, 0x54 // 4, E)))
            deref(d, it, D + 0x18, (0x54 - 0x18) // 4, E, '  ')
            nb0 = it.get(D + 8)
            for q in range(u(D + 4) or 0):
                nb = nb0 + 28 * q
                nm = P.cstr(d, it[nb + 8]) if nb + 8 in it else '?'
                print('  node %d %s @%#x: %s' % (q, nm, nb, words(d, it, nb, 7, E)))
                ac = it.get(nb + 0x18)
                for j in range(u(nb + 0x14) or 0):
                    if ac is None: break
                    a = ac + 0x10 * j
                    print('    action %d @%#x: %s' % (j, a, words(d, it, a, 4, E)))
                    deref(d, it, a, 4, E, '    ')
                ta = it.get(nb + 0x10)
                for j in range(u(nb + 0xc) or 0):
                    tt = it.get(ta + 4 * j) if ta is not None else None
                    if tt is None: continue
                    print('    trans %d @%#x: %s' % (j, tt, words(d, it, tt, 12, E)))
                    deref(d, it, tt, 12, E, '    ')
        return 0
    print('no uber block'); return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
