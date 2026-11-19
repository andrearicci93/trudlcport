"""R9 side check (2026-11-19): collision face FLAGS bytes (+0x0c..+0x0f) and +0x10 byte of a converted PC unit DRM
against the Xbox original, per TerrainGroup mesh: equal, bytes 2 / 3 exchanged, other. Read-only, counts only.

Usage (from the repository root):
  ../bin/pyt -t 600 work/r9_1911/r9_face_flags.py PC.drm XBOX.drm
"""
import sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r9_post_faces as P


def main(argv):
    if len(argv) != 2:
        sys.exit(__doc__)
    sides = []
    for path, e, f in ((argv[0], 'le', '<'), (argv[1], 'be', '>')):
        D, rel = P.load(path, e)
        sides.append([(gi, P.faces(D, h, f)) for gi, h in P.meshes(D, rel, f)])
    tot = collections.Counter()
    for (ga, fa), (gb, fb) in zip(sides[0], sides[1]):
        c = collections.Counter()
        samples = collections.Counter()
        for a, b in zip(fa, fb):
            if a is None or b is None:
                c['unreadable'] += 1; continue
            fl_a, fl_b = a[1], b[1]
            if fl_a == fl_b:
                k = 'equal'
            elif fl_a == fl_b[:2] + fl_b[3:4] + fl_b[2:3]:
                k = 'bytes 2/3 exchanged'
                samples['%s<-%s' % (fl_a.hex(), fl_b.hex())] += 1
            else:
                k = 'other'
                samples['%s<-%s' % (fl_a.hex(), fl_b.hex())] += 1
            c[k] += 1
            if a[2] != b[2]:
                c['+0x10 differs'] += 1
        tot.update(c)
        print('group %d: faces %d / %d  %s' % (ga, len(fa), len(fb), dict(c)))
        for s, n in samples.most_common(6):
            print('      PC<-Xbox %s x%d' % (s, n))
    print('total %s' % dict(tot))


if __name__ == '__main__':
    main(sys.argv[1:])
