"""R8 helper (read-only, 2026-11-18): every intro of one PC base unit with object name, position, script id, the
class chain and the instanceref targets of its members, plus the reverse list (who points at a given intro).
Output is game data: write it to <workspace>/local_results/, never into the repository.

Usage (from the repository root):
  ../bin/pyt -t 900 work/r8_1811/unit_intro_list.py UNIT [ID,ID...]
  ID = intros whose referrers are listed at the end (default none)
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
import puzzle_switch_scan as PS


def main(argv):
    if not argv:
        print(__doc__); return 2
    unit = argv[0].lower()
    want = [int(x) for x in argv[1].split(',')] if len(argv) > 1 else []
    S = PS.Source('pc', None)
    secs = S.drm(unit)
    if not secs:
        print('unit %s not found' % unit); return 1
    intros = PS.intros_of(secs, S.e, S.names) or []
    pool = PS.Pool(S); pool.add_drm(secs)
    back = {}
    print('# unit %s: %d intros' % (unit, len(intros)))
    for it in intros:
        chain = pool.chain(it['script'], secs) if it['script'] else []
        cls = [sc.id for sc in chain or []]
        refs = []
        for sc in chain or []:
            for m in sc.members:
                if m['tid'] is not None and pool.native(m['tid'], secs) == 'instanceref':
                    v = sc.value32(m['val'], 0)
                    refs.append((sc.id, m['off'], v))
                    back.setdefault(v, []).append(it['uid'])
        print('%5d idx %3d obj %5d %-34s pos %9.1f %9.1f %9.1f script %s chain %s refs %s' % (
            it['uid'], it['idx'], it['obj'], it['name'], it['pos'][0], it['pos'][1], it['pos'][2], it['script'],
            cls[:4], ['c%d+%d->%s' % r for r in refs]))
    for w in want:
        print('# referrers of %d: %s' % (w, back.get(w, [])))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
