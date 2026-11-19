"""R9 (2026-11-19): collision faces of a unit DRM around a vertical line (the slanted wooden posts of dlc_dungeon), own
PC tree (little-endian) against the Xbox original (big-endian): vertices, FLAGS word, +0x10 byte per face, and the first
face a downward vertical ray from a start point meets (any facing, and only faces whose normal points up).

Layout as tools/collision_faces.py (TerrainGroup -> mesh header +0x20 position, +0x30 vertices, +0x34 faces 20 B).
Frame: live = mesh local + group position - Level+0x80 (same frame as the markup / intro tools); --frame plus uses
+ Level+0x80 instead (both are tried with 'auto').
Read-only; prints game geometry -> output goes to ../local_results, never into the repository.

Usage (from the repository root):
  ../bin/pyt -t 600 work/r9_1911/r9_post_faces.py PC.drm XBOX.drm X,Y,Z [--radius R] [--depth D]
"""
import sys, os, struct, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import drm_write as DW, drm_reloc as R


def load(path, e):
    D = DW.read(open(path, 'rb').read(), e)
    rel = []
    for s in D.sections:
        r = R.parse(bytes(s.reloc), e)
        rel.append((dict(r.internal), {so: (si, do) for si, so, do in r.external}))
    return D, rel


def target(rel, si, o):
    itn, ext = rel[si]
    if o in itn: return si, itn[o]
    if o in ext: return ext[o]
    return None


def meshes(D, rel, f):
    t = target(rel, 0, 0)
    if t is None: return []
    ti, to = t
    td = bytes(D.sections[ti].data)
    ntg = struct.unpack_from(f + 'i', td, to + 8)[0]
    groups = []
    g = target(rel, ti, to + 0xc)
    if g is not None: groups += [(g[0], g[1] + 0x50 * k) for k in range(ntg)]
    g2 = target(rel, ti, to + 0x10)
    if g2 is not None and g2 not in groups: groups.append(g2)
    out, seen = [], set()
    for gi, (gs, go) in enumerate(groups):
        m = target(rel, gs, go + 0x38)
        if m is None or m in seen: continue
        seen.add(m)
        ms, mo = m
        md = bytes(D.sections[ms].data)
        h = dict(pos=struct.unpack_from(f + '3f', md, mo + 0x20), nf=struct.unpack_from(f + 'I', md, mo + 0x44)[0],
                 nv=struct.unpack_from(f + 'I', md, mo + 0x48)[0], v=target(rel, ms, mo + 0x30),
                 fc=target(rel, ms, mo + 0x34))
        out.append((gi, h))
    return out


def faces(D, h, f):
    vs, vo = h['v']; fs, fo = h['fc']
    vd = bytes(D.sections[vs].data); fd = bytes(D.sections[fs].data) + b'\0' * 4
    V = [struct.unpack_from(f + '3f', vd, vo + 16 * k) for k in range(h['nv'])]
    out = []
    for k in range(h['nf']):
        o = fo + 20 * k
        i0, i1, i2 = struct.unpack_from(f + '3I', fd, o)
        flags = fd[o + 12:o + 16]
        b10 = fd[o + 16]
        if max(i0, i1, i2) >= len(V):
            out.append(None); continue
        out.append(((V[i0], V[i1], V[i2]), flags, b10))
    return out


def ray_down(tri, x, y):
    """z where the vertical line through (x, y) meets the triangle (None if outside), and the normal z"""
    (ax, ay, az), (bx, by, bz), (cx, cy, cz) = tri
    det = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
    if abs(det) < 1e-9: return None, 0.0
    l1 = ((by - cy) * (x - cx) + (cx - bx) * (y - cy)) / det
    l2 = ((cy - ay) * (x - cx) + (ax - cx) * (y - cy)) / det
    l3 = 1 - l1 - l2
    if min(l1, l2, l3) < -1e-6: return None, 0.0
    ux, uy, uz = bx - ax, by - ay, bz - az
    wx, wy, wz = cx - ax, cy - ay, cz - az
    nx, ny, nz = uy * wz - uz * wy, uz * wx - ux * wz, ux * wy - uy * wx
    ln = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    return l1 * az + l2 * bz + l3 * cz, nz / ln


def main(argv):
    if len(argv) < 3:
        sys.exit(__doc__)
    rad, depth = 150.0, 1200.0
    if '--radius' in argv: k = argv.index('--radius'); rad = float(argv[k + 1]); del argv[k:k + 2]
    if '--depth' in argv: k = argv.index('--depth'); depth = float(argv[k + 1]); del argv[k:k + 2]
    sx, sy, sz = (float(v) for v in argv[2].split(','))
    sides = []
    for path, e, f in ((argv[0], 'le', '<'), (argv[1], 'be', '>')):
        D, rel = load(path, e)
        origin = struct.unpack_from(f + '3f', bytes(D.sections[0].data), 0x80)
        ms = meshes(D, rel, f)
        sides.append((path, f, D, origin, ms))
    for path, f, D, origin, ms in sides:
        print('%s: %d collision meshes, %d faces, Level+0x80 %.1f %.1f %.1f'
              % (path, len(ms), sum(h['nf'] for _, h in ms), origin[0], origin[1], origin[2]))
    for frame_sign in (-1.0, 0.0, 1.0):
        print('== frame: live = local + group pos %s Level+0x80' % {-1.0: '-', 0.0: '(no)', 1.0: '+'}[frame_sign])
        res = []
        for path, f, D, origin, ms in sides:
            near, hits = {}, []
            for gi, h in ms:
                px, py, pz = h['pos']
                off = (px + frame_sign * origin[0], py + frame_sign * origin[1], pz + frame_sign * origin[2])
                for k, fc in enumerate(faces(D, h, f)):
                    if fc is None: continue
                    tri = tuple(tuple(v[j] + off[j] for j in range(3)) for v in fc[0])
                    cx = sum(v[0] for v in tri) / 3; cy = sum(v[1] for v in tri) / 3; cz = sum(v[2] for v in tri) / 3
                    if math.hypot(cx - sx, cy - sy) <= rad and sz - depth <= cz <= sz + 100:
                        near[(gi, k)] = (tri, fc[1], fc[2])
                    z, nz = ray_down(tri, sx, sy)
                    if z is not None and sz - depth <= z <= sz + 5:
                        hits.append((sz - z, z, nz, gi, k, fc[1].hex(), fc[2]))
            hits.sort()
            res.append((path, near, hits))
            print('%s: faces near %d; vertical ray from %.1f / %.1f / %.1f meets %d faces within %.0f below:'
                  % (os.path.basename(os.path.dirname(path)) + '/' + os.path.basename(path), len(near), sx, sy, sz,
                     len(hits), depth))
            for d, z, nz, gi, k, fl, b in hits[:12]:
                print('   drop %7.1f  z %8.1f  normal z %+.3f  group %d face %d  flags %s  +0x10 %d' % (d, z, nz, gi, k, fl, b))
        if len(res) == 2 and res[0][1] and res[1][1]:
            a, b = res[0][1], res[1][1]
            same_keys = set(a) & set(b)
            diff_flags = [k for k in same_keys if a[k][1] != b[k][1][::-1] and a[k][1] != b[k][1]]
            swapped = [k for k in same_keys if a[k][1] == b[k][1][::-1] and a[k][1] != b[k][1]]
            equal = [k for k in same_keys if a[k][1] == b[k][1]]
            geo = [k for k in same_keys if max(abs(a[k][0][i][j] - b[k][0][i][j]) for i in range(3) for j in range(3)) > 0.01]
            print('near faces PC %d / Xbox %d, same (group, face) %d: flags equal bytes %d, reversed %d, other %d; '
                  'vertices differ %d' % (len(a), len(b), len(same_keys), len(equal), len(swapped), len(diff_flags), len(geo)))
            for k in sorted(diff_flags)[:10]:
                print('   flags differ %s: PC %s Xbox %s' % (k, a[k][1].hex(), b[k][1].hex()))


if __name__ == '__main__':
    main(sys.argv[1:])
