"""R9 (2026-11-19): full matrix, local and live points of chosen unit markup2 items (perch / pillar posts of
dlc_dungeon), plus the item axis tilt (read-only).

Usage (from the repository root):
  ../bin/pyt -t 600 work/r9_1911/r9_items.py UNIT.drm [--be] ID[,ID..]
"""
import sys, os, struct, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
import drm_write as DW, drm_reloc as R
import markup_level as ML


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    be = '--be' in argv
    argv = [a for a in argv if a != '--be']
    e = 'be' if be else 'le'
    f = '>' if be else '<'
    D = DW.read(open(argv[0], 'rb').read(), e)
    rel = []
    for s in D.sections:
        r = R.parse(bytes(s.reloc), e)
        rel.append((dict(r.internal), {o: (xi, t) for xi, o, t in r.external}))
    hd = bytes(D.sections[0].data)
    origin = struct.unpack_from(f + '3f', hd, 0x80)
    want = set(int(x) for x in argv[1].split(','))
    items, head = ML.markup2_items(D, rel, f, origin)
    print(head)
    print('Level+0x80 origin %.2f %.2f %.2f' % origin)
    for k, si, o, iid, aux, kind, typ, fl, pts in items:
        if iid not in want:
            continue
        d = bytes(D.sections[si].data)
        M = [struct.unpack_from(f + '4f', d, o + 16 * r) for r in range(4)]
        cnt = struct.unpack_from(f + 'i', d, o + 0x9c)[0]
        pp = ML.target(D, rel, si, o + 0xa0)
        loc = []
        if pp:
            pd = bytes(D.sections[pp[0]].data)
            for j in range(cnt):
                loc.append(struct.unpack_from(f + '8f', pd, pp[1] + 0x20 * j))
        print('id %d type %d kind %d flags50 0x%02x aux %d' % (iid, typ, kind, fl, aux))
        for r in range(4):
            print('  M row%d  %10.4f %10.4f %10.4f %10.4f' % ((r,) + M[r]))
        for j, l in enumerate(loc):
            print('  local p%d %s' % (j, ' '.join('%.3f' % v for v in l)))
        for j, p in enumerate(pts):
            print('  live  p%d %.2f %.2f %.2f' % (j, p[0], p[1], p[2]))
        if len(pts) == 2:
            dx, dy, dz = (pts[1][c] - pts[0][c] for c in range(3))
            ln = math.sqrt(dx * dx + dy * dy + dz * dz)
            ang = math.degrees(math.acos(abs(dz) / ln)) if ln else 0.0
            print('  segment length %.2f, dz %.2f, angle to vertical %.2f deg' % (ln, dz, ang))
        up = M[2][:3]
        n = math.sqrt(sum(v * v for v in up)) or 1.0
        print('  matrix row2 (local z) tilt vs world z %.2f deg' % math.degrees(math.acos(max(-1.0, min(1.0, up[2] / n)))))


if __name__ == '__main__':
    main(sys.argv[1:])
