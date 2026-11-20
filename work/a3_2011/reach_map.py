"""A3 helper (read-only, 2026-11-20): where the pushable Thor pillar can stand and which of those spots it can reach
from its start, from the unit's terrain collision meshes (live frame, ENGINE 9 "Thor pillar floor positions (R8b)").

Unlike R8b's floor_map.py (only faces flatter than 20 degrees, one sample per 150-u cell centre) this samples EVERY
collision face (walls, crate sides, boulders, the cage) densely and keeps per fine cell the highest surface point in
[FLOOR - 60, CAP] (CAP default floor + 1450 = above the pillar top 1408). Then
  * blocked cell: highest point - FLOOR > STEP (the height-step rule), or no surface at all in the cell (a hole);
  * valid pillar centre: no blocked cell within RP of it (the pillar foot is a disc of radius RP);
  * reachable: 8-connected flood fill over valid centres from START (pushing / pulling from any side);
  * per probe point (proven spots, track points): valid / reachable, distance to the nearest blocked cell (= how
    much foot radius would still fit) and the blocking height there;
  * targets (TARGETS.txt as for r8_1811/pillar_regions.py): gap D = flat distance to the ledge / ring - RTOP (the top
    grab ring, default 552) for every reachable centre, cells with D <= GAP per target;
  * --upper ZS:RTOP2 adds a second layer: surfaces above FLOOR + ZS block within RTOP2 (a wider top part), the foot
    test RP then only looks below FLOOR + ZS.
Default foot radius 285 = calibrated on the logged push tracks (all 454 resting points reachable at 285, 5 lost at 300).
Output is game data: write it to <workspace>/local_results/, never into the repository.

Usage (from the repository root):
  ../bin/pyt -t 1800 work/a3_2011/reach_map.py UNIT.drm --box X0,X1,Y0,Y1 [--cell 25] [--floor 173.1]
        [--cap Z] [--step 10] [--rp 285] [--rtop 552] [--upper ZS:R] [--start X,Y] [--targets T.txt] [--gap 600]
        [--probe NAME:X:Y ...] [--cells REGIONS.csv:D] [--tracks TRACKS.csv] [--map OUT.txt] [--mapcell 100] [--csv OUT.csv]
        [--sweep-rp R1,R2,...] [--sweep-step S1,S2,...]
"""
import sys, os, math, struct, collections
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
import collision_faces as CF


def seg_d(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay; L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def raster(path, x0, x1, y0, y1, cell, zlo, zhi):
    """hmax[ix, iy] = highest face sample in [zlo, zhi] (nan = none), cnt faces used"""
    D, rel = CF.load(path)
    nx = int(math.ceil((x1 - x0) / cell)); ny = int(math.ceil((y1 - y0) / cell))
    hmax = np.full(nx * ny, -1e9)
    used = 0
    bary = {}
    for gi, gid, ms, mo, h in CF.meshes(D, rel):
        vs, vo = h['v']; fs, fo = h['f']
        vd = D.sections[vs].data; fd = D.sections[fs].data + b'\0' * 4
        V = np.array([struct.unpack_from('<3f', vd, vo + 16 * k) for k in range(h['nv'])]) + np.array(h['pos'])
        for k in range(h['nf']):
            i0, i1, i2, fl = struct.unpack_from('<4I', fd, fo + 20 * k)
            if max(i0, i1, i2) >= len(V): continue
            P = V[[i0, i1, i2]]
            if P[:, 0].max() < x0 or P[:, 0].min() > x1 or P[:, 1].max() < y0 or P[:, 1].min() > y1: continue
            if P[:, 2].max() < zlo or P[:, 2].min() > zhi: continue
            used += 1
            L = max(np.linalg.norm(P[1] - P[0]), np.linalg.norm(P[2] - P[0]), np.linalg.norm(P[2] - P[1]))
            n = max(1, int(math.ceil(L / (cell * 0.4))))
            if n not in bary:
                ab = [(i / n, j / n) for i in range(n + 1) for j in range(n + 1 - i)]
                bary[n] = np.array(ab)
            ab = bary[n]
            S = P[0] + np.outer(ab[:, 0], P[1] - P[0]) + np.outer(ab[:, 1], P[2] - P[0])
            m = (S[:, 2] >= zlo) & (S[:, 2] <= zhi) & (S[:, 0] >= x0) & (S[:, 0] < x1) & (S[:, 1] >= y0) & (S[:, 1] < y1)
            if not m.any(): continue
            S = S[m]
            ix = ((S[:, 0] - x0) // cell).astype(int); iy = ((S[:, 1] - y0) // cell).astype(int)
            np.maximum.at(hmax, ix * ny + iy, S[:, 2])
    return hmax.reshape(nx, ny), used


def disc_offsets(rp, cell):
    r = int(math.ceil(rp / cell))
    return [(i, j) for i in range(-r, r + 1) for j in range(-r, r + 1) if math.hypot(i, j) * cell <= rp]


def dilate(blocked, offs):
    nx, ny = blocked.shape
    out = np.zeros_like(blocked)
    r = max(max(abs(i), abs(j)) for i, j in offs)
    pad = np.ones((nx + 2 * r, ny + 2 * r), dtype=bool)
    pad[r:r + nx, r:r + ny] = blocked
    for i, j in offs:
        out |= pad[r + i:r + i + nx, r + j:r + j + ny]
    return out


def flood(valid, s):
    nx, ny = valid.shape
    seen = np.zeros_like(valid)
    if not valid[s]: return seen
    q = collections.deque([s]); seen[s] = True
    while q:
        a, b = q.popleft()
        for da in (-1, 0, 1):
            for db in (-1, 0, 1):
                c, d = a + da, b + db
                if 0 <= c < nx and 0 <= d < ny and valid[c, d] and not seen[c, d]:
                    seen[c, d] = True; q.append((c, d))
    return seen


def main(argv):
    def opt(k, d):
        if k in argv:
            i = argv.index(k); v = argv[i + 1]; del argv[i:i + 2]; return v
        return d
    box = [float(v) for v in opt('--box', '-16000,-5000,-3600,5800').split(',')]
    cell = float(opt('--cell', '25')); floor = float(opt('--floor', '173.1'))
    cap = float(opt('--cap', str(floor + 1450))); step = float(opt('--step', '10')); rp = float(opt('--rp', '285'))
    start = [float(v) for v in opt('--start', '-9113,191').split(',')]
    tgt = opt('--targets', None); gap_max = float(opt('--gap', '600')); rtop = float(opt('--rtop', '552'))
    tracks = opt('--tracks', None); mapp = opt('--map', None); mapcell = float(opt('--mapcell', '100'))
    csvp = opt('--csv', None)
    sw_rp = opt('--sweep-rp', None); sw_st = opt('--sweep-step', None)
    probes = []
    while '--probe' in argv:
        i = argv.index('--probe'); n, x, y = argv[i + 1].split(':'); probes.append((n, float(x), float(y))); del argv[i:i + 2]
    cellcsv = opt('--cells', None)          # 'FILE.csv:D' = cells of r8_1811/pillar_regions.py --csv with that D
    cellpts = []
    if cellcsv:
        f, dsel = cellcsv.rsplit(':', 1)
        for line in open(f).read().splitlines()[1:]:
            p = line.split(',')
            if float(p[1]) == float(dsel): cellpts.append((p[0], float(p[2]), float(p[3])))
    if not argv:
        print(__doc__); return 2
    x0, x1, y0, y1 = box
    up = opt('--upper', None)
    upper = None
    if up:
        zs, rtop = [float(v) for v in up.split(':')]
        hup, _ = raster(argv[0], x0, x1, y0, y1, cell, floor + zs, cap)
        upper = (hup > -1e8, rtop, zs)
        cap = floor + zs
    hmax, used = raster(argv[0], x0, x1, y0, y1, cell, floor - 60, cap)
    nx, ny = hmax.shape
    if upper:
        print('# two layers: foot radius %.0f below floor + %.0f, top radius %.0f from there up to %.0f; %d upper cells'
              % (rp, upper[2], upper[1], floor + 1450, int(upper[0].sum())))
    rise = np.where(hmax < -1e8, np.inf, hmax - floor)
    print('# %s: %d faces sampled, grid %d x %d cells of %.0f u, box x %.0f..%.0f y %.0f..%.0f, floor %.1f, cap %.0f'
          % (os.path.basename(argv[0]), used, nx, ny, cell, x0, x1, y0, y1, floor, cap))
    bands = ((2, '0..2'), (6, '2..6'), (10, '6..10'), (20, '10..20'), (40, '20..40'), (100, '40..100'),
             (300, '100..300'), (1e18, '>300'))
    hist = collections.Counter()
    for v in rise.ravel():
        hist['hole' if not np.isfinite(v) else next(lab for b, lab in bands if v <= b)] += 1
    print('# cell rise above the floor (highest surface in the cell - floor): %s' % ', '.join(
        '%s %d' % (k, hist[k]) for k in ('0..2', '2..6', '6..10', '10..20', '20..40', '40..100', '100..300', '>300', 'hole')))

    def cidx(x, y):
        return int((x - x0) // cell), int((y - y0) // cell)

    def ccen(i, j):
        return x0 + (i + 0.5) * cell, y0 + (j + 0.5) * cell

    def solve(rp_, step_):
        blocked = ~(rise <= step_)
        valid = ~dilate(blocked, disc_offsets(rp_, cell))
        if upper:
            valid &= ~dilate(upper[0], disc_offsets(upper[1], cell))
        reach = flood(valid, cidx(*start))
        return blocked, valid, reach

    track_pts = []
    if tracks:
        for line in open(tracks).read().splitlines()[1:]:
            p = line.split(',')
            if float(p[7]) > 179.0: continue          # bounce frames at the stop (z up to +21), not resting contact
            track_pts.append((float(p[5]), float(p[6])))

    def near_block(blocked, x, y, lim=900):
        i, j = cidx(x, y); r = int(lim / cell) + 1
        best = (1e9, None)
        for a in range(max(0, i - r), min(nx, i + r + 1)):
            for b in range(max(0, j - r), min(ny, j + r + 1)):
                if blocked[a, b]:
                    cx, cy = ccen(a, b); d = math.hypot(cx - x, cy - y)
                    if d < best[0]: best = (d, (cx, cy, rise[a, b]))
        return best

    if sw_rp or sw_st:
        print('# sweep: foot radius RP x height step STEP -> valid / reachable centres, track points valid, probes')
        for st in [float(v) for v in (sw_st or str(step)).split(',')]:
            for r_ in [float(v) for v in (sw_rp or str(rp)).split(',')]:
                bl, va, re_ = solve(r_, st)
                tv = sum(1 for x, y in track_pts if 0 <= cidx(x, y)[0] < nx and 0 <= cidx(x, y)[1] < ny and re_[cidx(x, y)])
                pr = ' '.join('%s=%s' % (n, 'R' if re_[cidx(x, y)] else ('v' if va[cidx(x, y)] else '-')) for n, x, y in probes)
                print('  step %5.1f rp %4.0f: valid %6d reachable %6d, track points reachable %d / %d, %s' % (
                    st, r_, int(va.sum()), int(re_.sum()), tv, len(track_pts), pr))

    blocked, valid, reach = solve(rp, step)
    print('# step %.1f, rp %.0f: blocked %d, valid centres %d, reachable from start (%.0f, %.0f) %d (%.2f M u2)' % (
        step, rp, int(blocked.sum()), int(valid.sum()), start[0], start[1], int(reach.sum()), reach.sum() * cell * cell / 1e6))
    for n, x, y in probes:
        i, j = cidx(x, y)
        d, w = near_block(blocked, x, y)
        print('probe %-10s (%.0f, %.0f): valid %s, reachable %s, nearest blocked cell %.0f u away%s' % (
            n, x, y, bool(valid[i, j]), bool(reach[i, j]), d,
            ' at (%.0f, %.0f) rise %s' % (w[0], w[1], 'hole' if not np.isfinite(w[2]) else '%.0f' % w[2]) if w else ''))
    if cellpts:
        per = collections.OrderedDict()
        for n, x, y in cellpts:
            i, j = cidx(x, y)
            ok = 0 <= i < nx and 0 <= j < ny and bool(reach[i, j])
            per.setdefault(n, [0, 0])[0 if ok else 1] += 1
        print('# --cells %s: %d cells; per target reachable / not reachable: %s' % (
            cellcsv, len(cellpts), ', '.join('%s %d / %d' % (k, v[0], v[1]) for k, v in per.items())))
    if track_pts:
        ds =[near_block(blocked, x, y)[0] for x, y in track_pts]
        nv = sum(1 for x, y in track_pts if not reach[cidx(x, y)])
        print('# track points (resting z <= 179): %d, not reachable here %d, nearest blocked cell min %.0f / median %.0f u'
              % (len(track_pts), nv, min(ds), sorted(ds)[len(ds) // 2]))
        worst = sorted(zip(ds, track_pts))[:8]
        for d, (x, y) in worst:
            _, w = near_block(blocked, x, y)
            print('   track (%.0f, %.0f): nearest blocked %.0f u at (%.0f, %.0f) rise %s' % (
                x, y, d, w[0], w[1], 'hole' if not np.isfinite(w[2]) else '%.0f' % w[2]))

    targets = []
    if tgt:
        for line in open(tgt).read().splitlines():
            p = line.split('#')[0].split()
            if not p: continue
            if p[1] == 'ring':
                targets.append((p[0], 'ring', float(p[5]), (float(p[2]), float(p[3]), float(p[4]))))
            else:
                v = [float(q) for q in p[3:]]
                targets.append((p[0], 'line', float(p[2]), list(zip(v[0::2], v[1::2]))))
    ri, rj = np.nonzero(reach)
    rc = [ccen(a, b) for a, b in zip(ri, rj)]
    rows = []
    for name, kind, tz, geo in targets:
        def gap(x, y):
            if kind == 'ring':
                cx, cy, rr = geo; return math.hypot(x - cx, y - cy) - rr - rtop
            return min(seg_d(x, y, *geo[k], *geo[k + 1]) for k in range(len(geo) - 1)) - rtop
        g = [(gap(x, y), x, y) for x, y in rc]
        inn = [t for t in g if t[0] <= gap_max]
        best = min(g) if g else None
        if inn:
            xs = [t[1] for t in inn]; ys = [t[2] for t in inn]
            print('target %-6s z %5.0f: %5d reachable centres with D <= %.0f (%.2f M u2), bbox x %.0f..%.0f y %.0f..%.0f, '
                  'min D %.0f at (%.0f, %.0f)' % (name, tz, len(inn), gap_max, len(inn) * cell * cell / 1e6, min(xs), max(xs),
                                                  min(ys), max(ys), best[0], best[1], best[2]))
        elif best:
            print('target %-6s z %5.0f: none within D %.0f, min D %.0f at (%.0f, %.0f)' % (name, tz, gap_max, *best))
        for n, x, y in probes:
            print('   %-10s D to %-6s %6.0f' % (n, name, gap(x, y)))
        rows += [(name, x, y, d) for d, x, y in inn]
    if csvp:
        with open(csvp, 'w') as fh:
            fh.write('target,x,y,gap\n')
            for r in rows: fh.write('%s,%.0f,%.0f,%.0f\n' % r)
    if mapp:
        k = max(1, int(round(mapcell / cell)))
        with open(mapp, 'w') as fh:
            fh.write('# map %.0f u per char (x %.0f..%.0f left -> right, y top = max): R reachable centre, v valid but '
                     'not reachable, . floor (rise <= step) but no room for the foot, 1..9 rise /20 u, # higher / wall, '
                     '_ hole; S start, P probes\n' % (k * cell, x0, x1))
            pm = {cidx(*start)[0] // k * 100000 + cidx(*start)[1] // k: 'S'}
            for n, x, y in probes:
                i, j = cidx(x, y); pm[i // k * 100000 + j // k] = 'P'
            for J in range((ny - 1) // k, -1, -1):
                row = []
                for I in range(nx // k + (1 if nx % k else 0)):
                    sl = (slice(I * k, min(nx, I * k + k)), slice(J * k, min(ny, J * k + k)))
                    key = I * 100000 + J
                    if key in pm: row.append(pm[key]); continue
                    if reach[sl].any(): row.append('R')
                    elif valid[sl].any(): row.append('v')
                    else:
                        rr = rise[sl]; rmax = np.max(np.where(np.isfinite(rr), rr, -1))
                        if not np.isfinite(rr).any(): row.append('_')
                        elif rmax <= step: row.append('.')
                        elif rmax <= 180: row.append(str(min(9, max(1, int(rmax // 20)))))
                        else: row.append('#')
                fh.write('%7.0f %s\n' % (y0 + (J * k + 0.5 * k) * cell, ''.join(row)))
        print('# map written: %s' % mapp)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
