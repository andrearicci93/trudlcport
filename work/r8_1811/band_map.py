"""R8b helper (read-only, 2026-11-18): symbol map of floor bands from the cell CSV of floor_map.py --csv.
Each band is SYMBOL:ZLO:ZHI; per cell the highest band hit wins (later bands override earlier ones when both hit);
'.' = floor below / between the bands, ' ' = no floor at all. Optional points NAME:X:Y are printed as their first
letter (upper case) over the map.

Usage (from the repository root):
  ../bin/pyt -t 120 work/r8_1811/band_map.py CELLS.csv CELL XMIN,XMAX,YMIN,YMAX BAND [BAND ...] [--pt NAME:X:Y ...]
"""
import sys


def radial(path, cx, cy, zlo, zhi, step, rmax):
    """lowest floor height (in [zlo, zhi)) per cell, binned by the distance to (cx, cy): n, mean, min, max per bin"""
    low = {}
    for line in open(path).read().splitlines()[1:]:
        x, y, z = [float(v) for v in line.split(',')]
        if zlo <= z < zhi and ((x, y) not in low or z < low[(x, y)]): low[(x, y)] = z
    bins = {}
    for (x, y), z in low.items():
        r = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
        if r < rmax: bins.setdefault(int(r // step) * int(step), []).append(z)
    print('# lowest floor in [%.0f, %.0f) against the distance to (%.0f, %.0f), bins of %.0f' % (zlo, zhi, cx, cy, step))
    for b in sorted(bins):
        v = bins[b]
        print('  r %5d n %3d mean %6.1f min %6.1f max %6.1f' % (b, len(v), sum(v) / len(v), min(v), max(v)))
    return 0


def main(argv):
    if '--radial' in argv:          # band_map.py CELLS.csv --radial CX,CY [ZLO,ZHI,STEP,RMAX]
        i = argv.index('--radial'); cx, cy = [float(v) for v in argv[i + 1].split(',')]
        zlo, zhi, step, rmax = [float(v) for v in (argv[i + 2] if len(argv) > i + 2 else '150,1000,100,1800').split(',')]
        return radial(argv[0], cx, cy, zlo, zhi, step, rmax)
    pts = []
    while '--pt' in argv:
        i = argv.index('--pt'); n, x, y = argv[i + 1].split(':'); pts.append((n, float(x), float(y))); del argv[i:i + 2]
    if len(argv) < 4:
        print(__doc__); return 2
    cell = float(argv[1]); x0, x1, y0, y1 = [float(v) for v in argv[2].split(',')]
    bands = []
    for b in argv[3:]:
        s, lo, hi = b.split(':'); bands.append((s, float(lo), float(hi)))
    nx = int((x1 - x0) // cell) + 1; ny = int((y1 - y0) // cell) + 1
    g = {}
    for line in open(argv[0]).read().splitlines()[1:]:
        x, y, z = [float(v) for v in line.split(',')]
        ix = int((x - x0) // cell); iy = int((y - y0) // cell)
        if not (0 <= ix < nx and 0 <= iy < ny): continue
        cur = g.get((ix, iy), '.')
        for s, lo, hi in bands:
            if lo <= z < hi: cur = s
        g[(ix, iy)] = cur
    for n, x, y in pts:
        ix = int((x - x0) // cell); iy = int((y - y0) // cell)
        if 0 <= ix < nx and 0 <= iy < ny: g[(ix, iy)] = n[0].upper()
    print('# x %.0f .. %.0f left to right, y %.0f .. %.0f top = max y, cell %.0f; bands %s; points %s' % (
        x0, x1, y0, y1, cell, ' '.join('%s=[%.0f,%.0f)' % b for b in bands), ' '.join('%s=%s(%.0f %.0f)' % (p[0][0].upper(), p[0], p[1], p[2]) for p in pts)))
    for iy in range(ny - 1, -1, -1):
        print('%7.0f %s' % (y0 + (iy + 0.5) * cell, ''.join(g.get((ix, iy), ' ') for ix in range(nx))))
    # connected components (4-neighbour) per band symbol: cells, centre, bbox (cell centres)
    print('# components per band (cells, centre x y, bbox x / y)')
    seen = set()
    for key in sorted(g):
        s = g[key]
        if s in '. ' or key in seen or s == s.upper() and s.isalpha() and s not in [b[0] for b in bands]: continue
        comp = []; todo = [key]; seen.add(key)
        while todo:
            c = todo.pop(); comp.append(c)
            for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (c[0] + d[0], c[1] + d[1])
                if q not in seen and g.get(q) == s: seen.add(q); todo.append(q)
        xs = [x0 + (c[0] + 0.5) * cell for c in comp]; ys = [y0 + (c[1] + 0.5) * cell for c in comp]
        print('  %s cells %4d centre %7.0f %7.0f bbox x %.0f..%.0f y %.0f..%.0f' % (
            s, len(comp), sum(xs) / len(xs), sum(ys) / len(ys), min(xs), max(xs), min(ys), max(ys)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
