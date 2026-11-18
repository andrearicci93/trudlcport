"""R8b helper (read-only, 2026-11-18): floor height map of a unit's collision meshes in a live-frame box.

Rasterises every collision face whose slope is below --slope degrees (default 20) onto a square grid (--cell units,
default 100) by sampling the cell centres inside the triangle (plane height there). Per cell all floor heights are
kept. Output (game data, local only):
  * histogram of floor heights (rounded to 10 u) inside the box
  * map of the lowest floor band: one char per cell, '.' = floor height in [ZLO, ZLO+STEP), digits = steps of STEP
    above, '#' = no floor face below ZMAX, '+' = higher than 9 steps
  * --csv FILE: every cell 'x,y,z' (live frame, cell centre, each floor height below ZMAX)
Frame: live = data - ORIGIN (ORIGIN = Level+0x80 as printed by tools/markup_level.py).

Usage (from the repository root):
  ../bin/pyt -t 900 work/r8_1811/floor_map.py UNIT.drm ORIGIN_X,Y,Z XMIN,XMAX,YMIN,YMAX ZLO,STEP,ZMAX
        [--cell N] [--slope DEG] [--csv FILE]
"""
import sys, os, math, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
import collision_faces as CF


def main(argv):
    def opt(k, d):
        if k in argv:
            i = argv.index(k); v = argv[i + 1]; del argv[i:i + 2]; return v
        return d
    cell = float(opt('--cell', '100')); slope_max = float(opt('--slope', '20')); csvp = opt('--csv', None)
    if len(argv) < 4:
        print(__doc__); return 2
    org = [float(x) for x in argv[1].split(',')]
    x0, x1, y0, y1 = [float(x) for x in argv[2].split(',')]
    zlo, step, zmax = [float(x) for x in argv[3].split(',')]
    D, rel = CF.load(argv[0])
    nx = int((x1 - x0) // cell) + 1; ny = int((y1 - y0) // cell) + 1
    grid = collections.defaultdict(set)
    nfaces = 0
    for gi, gid, ms, mo, h in CF.meshes(D, rel):
        vs, vo = h['v']; fs, fo = h['f']
        vd = D.sections[vs].data; fd = D.sections[fs].data + b'\0' * 4
        import struct
        V = [struct.unpack_from('<3f', vd, vo + 16 * k) for k in range(h['nv'])]
        px, py, pz = h['pos']
        for k in range(h['nf']):
            i0, i1, i2, fl = struct.unpack_from('<4I', fd, fo + 20 * k)
            if max(i0, i1, i2) >= len(V): continue
            P = [(V[i][0] + px - org[0], V[i][1] + py - org[1], V[i][2] + pz - org[2]) for i in (i0, i1, i2)]
            u = [P[1][j] - P[0][j] for j in range(3)]; w = [P[2][j] - P[0][j] for j in range(3)]
            n = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0])
            ln = math.sqrt(sum(c * c for c in n)) or 1.0
            if abs(n[2]) / ln < math.cos(math.radians(slope_max)) or abs(n[2]) < 1e-9: continue
            if max(p[0] for p in P) < x0 or min(p[0] for p in P) > x1: continue
            if max(p[1] for p in P) < y0 or min(p[1] for p in P) > y1: continue
            if min(p[2] for p in P) > zmax: continue
            nfaces += 1
            ix0 = max(0, int((min(p[0] for p in P) - x0) // cell)); ix1 = min(nx - 1, int((max(p[0] for p in P) - x0) // cell))
            iy0 = max(0, int((min(p[1] for p in P) - y0) // cell)); iy1 = min(ny - 1, int((max(p[1] for p in P) - y0) // cell))
            den = (P[1][1] - P[2][1]) * (P[0][0] - P[2][0]) + (P[2][0] - P[1][0]) * (P[0][1] - P[2][1])
            if abs(den) < 1e-9: continue
            for ix in range(ix0, ix1 + 1):
                for iy in range(iy0, iy1 + 1):
                    cx = x0 + (ix + 0.5) * cell; cy = y0 + (iy + 0.5) * cell
                    a = ((P[1][1] - P[2][1]) * (cx - P[2][0]) + (P[2][0] - P[1][0]) * (cy - P[2][1])) / den
                    b = ((P[2][1] - P[0][1]) * (cx - P[2][0]) + (P[0][0] - P[2][0]) * (cy - P[2][1])) / den
                    c = 1 - a - b
                    if min(a, b, c) < -1e-6: continue
                    z = a * P[0][2] + b * P[1][2] + c * P[2][2]
                    if z <= zmax: grid[(ix, iy)].add(round(z, 1))
    hist = collections.Counter(round(z, -1) for s in grid.values() for z in s)
    print('# floor faces used %d, cells with floor %d of %d (cell %.0f u, slope < %.0f deg)' % (
        nfaces, len(grid), nx * ny, cell, slope_max))
    print('# floor height histogram (live z rounded to 10 u: cells)')
    for z in sorted(hist): print('  z %7.0f : %d' % (z, hist[z]))
    print('# map of the lowest floor: x %.0f .. %.0f (columns, left to right), y %.0f .. %.0f (rows, top = max y)' % (x0, x1, y0, y1))
    print('# . = [%.0f, %.0f), digit k = k steps of %.0f higher, + = higher, # = none' % (zlo, zlo + step, step))
    for iy in range(ny - 1, -1, -1):
        row = []
        for ix in range(nx):
            s = [z for z in grid.get((ix, iy), ()) if z >= zlo - 100]      # ignore rooms far below
            if not s: row.append('#'); continue
            z = min(s); k = int((z - zlo) // step)
            row.append('.' if k == 0 else ('-' if k < 0 else (str(k) if k <= 9 else '+')))
        print('%7.0f %s' % (y0 + (iy + 0.5) * cell, ''.join(row)))
    if csvp:
        with open(csvp, 'w') as fh:
            fh.write('x,y,z\n')
            for (ix, iy), s in sorted(grid.items()):
                for z in sorted(s):
                    fh.write('%.0f,%.0f,%.1f\n' % (x0 + (ix + 0.5) * cell, y0 + (iy + 0.5) * cell, z))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
