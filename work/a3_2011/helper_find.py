"""A3 helper (read-only, 2026-11-20): every intro of the PC base units whose object name contains a word (default
'collision_helper'), with unit, intro id, object id, data position and the unit's intro id range.
Output is game data: write it to <workspace>/local_results/, never into the repository.

Usage (from the repository root):
  ../bin/pyt -t 1800 work/a3_2011/helper_find.py [WORD] [GROUP]
  GROUP = unit group prefix (default l3)
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
import puzzle_switch_scan as PS


def main(argv):
    word = argv[0].lower() if argv else 'collision_helper'
    grp = argv[1] if len(argv) > 1 else 'l3'
    S = PS.Source('pc', None)
    for unit, g in S.units:
        if g != grp: continue
        secs = S.drm(unit)
        if not secs: continue
        intros = PS.intros_of(secs, S.e, S.names) or []
        ids = [it['uid'] for it in intros]
        rng = '%d..%d' % (min(ids), max(ids)) if ids else '-'
        hits = [it for it in intros if word in (it['name'] or '').lower()]
        print('%-28s %4d intros %s' % (unit, len(intros), rng))
        for it in hits:
            print('   HIT %5d obj %5d %-36s pos %9.1f %9.1f %9.1f script %s' % (
                it['uid'], it['obj'], it['name'], it['pos'][0], it['pos'][1], it['pos'][2], it['script']))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
