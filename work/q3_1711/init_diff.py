"""Read-only: member init trees of one script in two g_pda files (A, B; spec like work/crash_gpda_1411/sec_hex.py),
leaf by leaf (path = word offsets from the member's init root), every differing leaf and every shape difference.
Usage (repo root): ../bin/pyt work/q3_1711/init_diff.py SPEC_A SPEC_B SCRIPT_ID [--all]"""
import sys, os, struct
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'crash_gpda_1411'))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
from sec_hex import load
import drm_reloc as R, script_conv as SC
import script_member_pairs as MP
import script_init_from_pc as SIP


def view(spec, sid):
    e, S = load(spec)
    d, rl = [(x[2], x[3]) for x in S if x[0] == 8 and x[1] == sid][0]
    W, E = MP.entries(d, rl, e)
    return e, d, W, E


def main(argv):
    show_all = '--all' in argv
    argv = [a for a in argv if a != '--all']
    ea, da, Wa, Ea = view(argv[0], int(argv[2]))
    eb, db, Wb, Eb = view(argv[1], int(argv[2]))
    fa, fb = ('>' if ea == 'be' else '<'), ('>' if eb == 'be' else '<')
    for kind in Ea:
        A = {q['name']: q for q in Ea[kind]}; B = {q['name']: q for q in Eb[kind]}
        for nm in list(A) + [n for n in B if n not in A]:
            qa, qb = A.get(nm), B.get(nm)
            if qa is None or qb is None:
                print('%s name 0x%x only in %s' % (kind, nm, 'A' if qb is None else 'B')); continue
            la = list(SIP.leaves(Wa, Wa.it, qa['init'])) if qa['init'] is not None else []
            lb = list(SIP.leaves(Wb, Wb.it, qb['init'])) if qb['init'] is not None else []
            pa = [p for p, _ in la]; pb = [p for p, _ in lb]
            head = '%s #%d/#%d name 0x%x tag %d/%d ut %d/%d leaves %d/%d' % (
                kind, qa['k'], qb['k'], nm, qa['tag'], qb['tag'], qa['ut'], qb['ut'], len(la), len(lb))
            if pa != pb:
                print(head + '  SHAPE DIFFERS')
                sa, sb = set(pa), set(pb)
                for p in sorted(sa - sb): print('   only A %s' % (list(p),))
                for p in sorted(sb - sa): print('   only B %s' % (list(p),))
            diff = []
            mb = dict(lb)
            for p, oa in la:
                ob = mb.get(p)
                if ob is None: continue
                wa = struct.unpack_from(fa + 'I', da, oa)[0]; wb = struct.unpack_from(fb + 'I', db, ob)[0]
                if wa != wb or show_all: diff.append((p, oa, ob, wa, wb))
            if pa == pb and not diff and not show_all and qa['ut'] == qb['ut']: continue
            if pa == pb: print(head)
            for p, oa, ob, wa, wb in diff:
                print('   %-22s A +0x%05x %08x  B +0x%05x %08x%s' % (list(p), oa, wa, ob, wb, '' if wa != wb else '  ='))


if __name__ == '__main__':
    main(sys.argv[1:])
