"""Read-only: which members / args / locals in the scripts of DRMs use the given userTypes, and which script roots
hold the value as a u16 in their first 0x54 bytes (type id candidates).
Usage (repo root): ../bin/pyt -t 900 work/crash_gpda_1411/ut_users.py UT[,UT...] SPEC [SPEC ...]"""
import sys, os, struct
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
from sec_hex import load
import script_member_pairs as MP


def main(argv):
    uts = {int(x) for x in argv[0].split(',')}
    for spec in argv[1:]:
        _, S = load(spec)
        for t, i, d, rl in S:
            if t != 8 or not d: continue
            try: _, E = MP.entries(d, rl, 'le')
            except Exception: continue
            for k, lst in E.items():
                for q in lst:
                    if q['ut'] in uts: print('%s script %d %s #%d tag %d ut %d name 0x%x' % (spec, i, k, q['k'], q['tag'], q['ut'], q['name']))
            hdr = [o for o in range(0, min(0x54, len(d)) - 1, 2) if struct.unpack_from('<H', d, o)[0] in uts]
            if hdr: print('%s script %d root u16 at %s = %s' % (spec, i, ['0x%x' % o for o in hdr], [struct.unpack_from('<H', d, o)[0] for o in hdr]))


if __name__ == '__main__':
    main(sys.argv[1:])
