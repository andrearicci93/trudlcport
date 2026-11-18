"""R8b helper (read-only, 2026-11-18): every markup2 item of a unit DRM with ALL poly line points in the live frame
(tools/markup_level.markup2_items; origin = Level+0x80 of the file unless given), plus bbox, centroid and a
closed / open flag. Optional --point X,Y,Z: horizontal and vertical distance of each item's nearest point to it.
Output is game data: write it to <workspace>/local_results/, never into the repository.

Usage (from the repository root):
  ../bin/pyt -t 120 work/r8_1811/markup_full.py UNIT.drm [--origin X,Y,Z] [--point X,Y,Z]
"""
import sys, os, struct
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
import drm_write as DW, drm_reloc as R
import markup_level as ML


def main(argv):
    def opt(k):
        if k in argv:
            i = argv.index(k); v = argv[i + 1]; del argv[i:i + 2]; return tuple(float(x) for x in v.split(','))
        return None
    origin = opt('--origin'); point = opt('--point')
    if not argv:
        print(__doc__); return 2
    D = DW.read(open(argv[0], 'rb').read(), 'le')
    rel = []
    for s in D.sections:
        r = R.parse(bytes(s.reloc), 'le')
        rel.append((dict(r.internal), {o: (xi, t) for xi, o, t in r.external}))
    if origin is None:
        t = ML.target(D, rel, 0, 0) and (0, 0)
        origin = struct.unpack_from('<3f', bytes(D.sections[0].data), 0x80)
    items, head = ML.markup2_items(D, rel, '<', origin)
    print('# origin %.1f %.1f %.1f; %s' % (origin[0], origin[1], origin[2], head))
    for k, si, o, iid, aux, kind, typ, fl, pts in items or []:
        if not pts: continue
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]; zs = [p[2] for p in pts]
        closed = len(pts) > 2 and sum((pts[0][c] - pts[-1][c]) ** 2 for c in range(3)) < 1.0
        cx = sum(xs[:-1] if closed else xs) / (len(pts) - (1 if closed else 0))
        cy = sum(ys[:-1] if closed else ys) / (len(pts) - (1 if closed else 0))
        extra = ''
        if point:
            best = min(pts, key=lambda p: (p[0] - point[0]) ** 2 + (p[1] - point[1]) ** 2)
            extra = ' nearest to point: dxy %.0f dz %.0f' % (
                ((best[0] - point[0]) ** 2 + (best[1] - point[1]) ** 2) ** 0.5, best[2] - point[2])
        print('item %2d id %4d %-12s %s n %2d bbox x %.0f..%.0f y %.0f..%.0f z %.1f..%.1f centre %.0f %.0f%s' % (
            k, iid, ML.tname(typ), 'closed' if closed else 'open  ', len(pts), min(xs), max(xs), min(ys), max(ys),
            min(zs), max(zs), cx, cy, extra))
        print('   pts ' + ' '.join('(%.0f %.0f %.0f)' % p for p in pts))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
