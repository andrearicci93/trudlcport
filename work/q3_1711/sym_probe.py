"""Read-only: what the converter's Symbol map (tools/dlc_generic.DlcIds.sym) makes of small integers - checks whether a
count word that came out one lower was mapped like a Symbol.
Usage (repo root): ../bin/pyt work/q3_1711/sym_probe.py VALUE [...]"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import dlc_generic as DG


def main(argv):
    I = DG.DlcIds()
    for v in argv:
        x = int(v, 0)
        ids_ = []
        for t in (5, 7, 8, 12):
            try: ids_.append('%d:%s' % (t, I(t, x)))
            except Exception as e: ids_.append('%d:err' % t)
        print('%d -> sym %s, section id map %s' % (x, I.sym(x), ' '.join(ids_)))


if __name__ == '__main__':
    main(sys.argv[1:])
