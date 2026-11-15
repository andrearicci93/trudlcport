"""Read-only: which DRMs of a list hold a section with the given id (any type).
Usage (repo root): ../bin/pyt -t 1800 work/crash_gpda_1411/find_section_id.py LIST.txt ID [...]"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import drm_write as DW


def main(argv):
    want = {int(x, 0) for x in argv[1:]}
    for f in open(argv[0], encoding='utf-8').read().split('\n'):
        f = f.strip()
        if not f: continue
        try: S = DW.read(open(f, 'rb').read(), 'le').sections
        except Exception as e: continue
        for s in S:
            if s.id in want: print('%s: type %d id %d size 0x%x' % (os.path.basename(f), s.type, s.id, len(s.data)))


if __name__ == '__main__':
    main(sys.argv[1:])
