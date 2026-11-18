"""R8b helper (read-only, 2026-11-18): floor areas where the round Thor pillar has to stand so that Lara, on its top,
is within a horizontal gap D of a target ledge, from the floor cell CSV of floor_map.py --csv (live frame).

Pillar (object data, ENGINE 9 "Thor pillar (R8)"): footprint radius RP (default 552 = its top grab ledge loop), top
at BASE + TOP (default 158 + 1250). A pillar centre cell is VALID when
  * every cell centre within RP of it has a floor height in [FLO, FHI] (default 150 .. 190 = the chamber floor) and
    no other face height in (FHI, CLEAR) (default 1700: steps of the middle platform, column rings, blocks); faces
    at or above CLEAR (galleries overhead) do not block,
  * gap = (horizontal distance of the centre to the target) - RP lies in [GMIN, D] (default GMIN 0),
  where the target is a ledge poly line (distance to its segments) or a column ring (centre + ring radius).
Per target and D: valid cells, bbox, centroid, the rise (target z - pillar top), a map, and --csv writes the cells.
Output is game data: write it to <workspace>/local_results/, never into the repository.

Usage (from the repository root):
  ../bin/pyt -t 600 work/r8_1811/pillar_regions.py CELLS.csv CELL TARGETS.txt D[,D...] [--rp R] [--top Z]
        [--base Z] [--floor LO,HI] [--clear Z] [--gmin G] [--csv OUT.csv]
  TARGETS.txt: one target per line 'NAME ring CX CY R Z' or 'NAME line Z X1 Y1 X2 Y2 ...' ('#' = comment)
"""
import sys, math, collections


def seg_d(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay; L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def main(argv):
    def opt(k, d):
        if k in argv:
            i = argv.index(k); v = argv[i + 1]; del argv[i:i + 2]; return v
        return d
    rp = float(opt('--rp', '552')); top = float(opt('--top', '1250')); base = float(opt('--base', '158'))
    flo, fhi = [float(v) for v in opt('--floor', '150,190').split(',')]; clear = float(opt('--clear', '1700'))
    gmin = float(opt('--gmin', '0')); csvp = opt('--csv', None)
    if len(argv) < 4:
        print(__doc__); return 2
    cell = float(argv[1]); Ds = [float(v) for v in argv[3].split(',')]
    targets = []
    for line in open(argv[2]).read().splitlines():
        p = line.split('#')[0].split()
        if not p: continue
        if p[1] == 'ring':
            targets.append((p[0], 'ring', float(p[5]), (float(p[2]), float(p[3]), float(p[4]))))
        else:
            v = [float(x) for x in p[3:]]
            targets.append((p[0], 'line', float(p[2]), list(zip(v[0::2], v[1::2]))))
    cells = collections.defaultdict(list)
    for line in open(argv[0]).read().splitlines()[1:]:
        x, y, z = [float(v) for v in line.split(',')]
        cells[(round(x), round(y))].append(z)
    floor_ok = {k for k, zs in cells.items() if any(flo <= z <= fhi for z in zs) and not any(fhi < z < clear for z in zs)}
    r = int(math.ceil(rp / cell))
    offs = [(i * cell, j * cell) for i in range(-r, r + 1) for j in range(-r, r + 1) if math.hypot(i * cell, j * cell) <= rp]
    fits = set()
    for (x, y) in floor_ok:
        if all((round(x + dx), round(y + dy)) in floor_ok for dx, dy in offs): fits.add((x, y))
    ptop = base + top
    print('# floor cells ok %d, pillar fits (radius %.0f) at %d cell centres; pillar top z %.0f' % (len(floor_ok), rp, len(fits), ptop))
    if '--map' in argv:
        argv.remove('--map')
        xs = sorted({k[0] for k in cells}); ys = sorted({k[1] for k in cells}, reverse=True)
        print('# map: F = pillar fits, o = floor ok (no blocker), b = floor with a blocker (height in (%.0f, %.0f)), '
              '^ = no chamber floor; x %d .. %d, y %d .. %d' % (fhi, clear, xs[0], xs[-1], ys[-1], ys[0]))
        for y in ys:
            row = []
            for x in xs:
                zs = cells.get((x, y), [])
                if (x, y) in fits: row.append('F')
                elif (x, y) in floor_ok: row.append('o')
                elif any(flo <= z <= fhi for z in zs): row.append('b')
                else: row.append('^' if zs else ' ')
            print('%7d %s' % (y, ''.join(row)))
    out = []
    for name, kind, tz, geo in targets:
        def gap(x, y):
            if kind == 'ring':
                cx, cy, rr = geo; return math.hypot(x - cx, y - cy) - rr - rp
            return min(seg_d(x, y, *geo[k], *geo[k + 1]) for k in range(len(geo) - 1)) - rp
        for D in Ds:
            v = sorted((x, y) for (x, y) in fits if gmin <= gap(x, y) <= D)
            if not v:
                print('%-10s D %4.0f: no cell (rise %.0f)' % (name, D, tz - ptop)); continue
            xs = [c[0] for c in v]; ys = [c[1] for c in v]
            print('%-10s D %4.0f: %4d cells, area %.2f M u2, centroid %.0f %.0f, bbox x %.0f..%.0f y %.0f..%.0f, rise %.0f, min gap %.0f' % (
                name, D, len(v), len(v) * cell * cell / 1e6, sum(xs) / len(xs), sum(ys) / len(ys), min(xs), max(xs), min(ys),
                max(ys), tz - ptop, min(gap(x, y) for x, y in v)))
            out += [(name, D, x, y, gap(x, y)) for x, y in v]
    if csvp:
        with open(csvp, 'w') as fh:
            fh.write('target,D,x,y,gap\n')
            for row in out: fh.write('%s,%.0f,%.0f,%.0f,%.0f\n' % row)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
