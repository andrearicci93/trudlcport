"""A3 helper (read-only, 2026-11-20): measured positions of a pushed object from TruMenu `[Push]` log lines
(start / move / end, TruMenu 0.22.59+), one row per line of the FIRST runtime id seen per push (the Thor pillar logs
both links with the same position). Prints per push: start, end, path length, and writes a CSV.

Line shape: `<date> <time> [Push] start|move|end <name> <id> pos=X Y Z rot=... hinge=H ... path=N (M m) T s`.
Output is game data: write it to <workspace>/local_results/, never into the repository.

Usage (from the repository root):
  ../bin/pyt -t 300 work/a3_2011/push_tracks.py LOG [NAME] [--csv OUT.csv]
  NAME default ma_pu_thor_pillar
"""
import sys, re

LINE = re.compile(r'^(\S+) (\S+) \[Push\] (start|move|end) (\S+) (\d+) pos=(-?[\d.]+) (-?[\d.]+) (-?[\d.]+) .*?hinge=(\S+)')


def main(argv):
    csvp = None
    if '--csv' in argv:
        i = argv.index('--csv'); csvp = argv[i + 1]; del argv[i:i + 2]
    if not argv:
        print(__doc__); return 2
    name = argv[1] if len(argv) > 1 else 'ma_pu_thor_pillar'
    rows, push, lead = [], 0, None
    for raw in open(argv[0], 'rb').read().decode('utf-8', 'replace').splitlines():
        m = LINE.match(raw)
        if not m or m.group(4) != name: continue
        d, t, kind, _, oid, x, y, z, h = m.groups()
        if kind == 'start' and (lead is None or lead_done):
            push += 1; lead = oid; lead_done = False
        if oid != lead: continue
        rows.append((push, d, t, kind, oid, float(x), float(y), float(z), h))
        if kind == 'end': lead_done = True
    print('# %d [Push] rows of %s (lead id per push), %d pushes' % (len(rows), name, push))
    for p in range(1, push + 1):
        r = [x for x in rows if x[0] == p]
        if not r: continue
        a, b = r[0], r[-1]
        xs = [x[5] for x in r]; ys = [x[6] for x in r]; zs = [x[7] for x in r]
        print('push %2d %s %s .. %s id %s: %.0f %.0f -> %.0f %.0f (%s, %d rows), x %.0f..%.0f y %.0f..%.0f z %.1f..%.1f' % (
            p, a[1], a[2], b[2], a[4], a[5], a[6], b[5], b[6], b[3], len(r), min(xs), max(xs), min(ys), max(ys),
            min(zs), max(zs)))
    if csvp:
        with open(csvp, 'w') as fh:
            fh.write('push,date,time,kind,id,x,y,z,hinge\n')
            for r in rows: fh.write('%d,%s,%s,%s,%s,%.1f,%.1f,%.1f,%s\n' % r)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
