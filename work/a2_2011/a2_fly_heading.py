"""A2 (2026-11-20): world direction of a logged jump (read only). For every TruMenu `[Jump] launch` line in a log
(optionally only those whose time starts with a prefix) the following `[Jump] fly f=.. p=x y z` samples give the
horizontal world step per frame; its heading h is printed in the game's convention forward = (sin h, -cos h)
(inst+0x38, as `MdDir`), together with the launch v and the logged text. With the launch v in Lara's frame
(x, -forward, up) the step must equal R(h) (v.x, v.y) - checked here as the predicted world step.

Usage (from the repository root):
  ../bin/pyt -t 60 work/a2_2011/a2_fly_heading.py LOG [TIME_PREFIX]
"""
import sys, re, math

FLY = re.compile(r'\[Jump\] fly f=(\d+) p=(-?[\d.]+) (-?[\d.]+) (-?[\d.]+)')
LAUNCH = re.compile(r'\[Jump\] launch via=(0x[0-9a-f]+).*? v=(-?[\d.]+) (-?[\d.]+) (-?[\d.]+) u/frame \(([^)]*)\)')


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    pre = argv[1] if len(argv) > 1 else ''
    cur = None
    for line in open(argv[0], encoding='utf-8', errors='replace'):
        m = LAUNCH.search(line)
        if m:
            if cur:
                report(cur)
            cur = None
            if line.startswith(pre):
                cur = {'t': line[:23], 'via': m.group(1), 'v': tuple(float(m.group(k)) for k in (2, 3, 4)),
                       'txt': m.group(5), 'fly': []}
            continue
        if cur is not None:
            f = FLY.search(line)
            if f:
                cur['fly'].append((int(f.group(1)), float(f.group(2)), float(f.group(3))))
            elif '[Jump] flight end' in line:
                report(cur)
                cur = None
    if cur:
        report(cur)
    return 0


def report(c):
    fl = c['fly']
    print('%s launch via %s v=(%.2f, %.2f, %.2f) logged "%s"' % (c['t'], c['via'], c['v'][0], c['v'][1], c['v'][2],
                                                                 c['txt']))
    if len(fl) < 2:
        print('  fewer than 2 fly samples')
        return
    (f0, x0, y0), (f1, x1, y1) = fl[0], fl[-1]
    n = f1 - f0
    dx, dy = (x1 - x0) / n, (y1 - y0) / n
    h = math.degrees(math.atan2(dx, -dy)) % 360.0
    vx, vy = c['v'][0], c['v'][1]
    r = math.radians(h)
    px, py = vx * math.cos(r) - vy * math.sin(r), vx * math.sin(r) + vy * math.cos(r)
    print('  world step per frame (%.2f, %.2f) |%.2f| over frames %d..%d -> heading %.1f deg; '
          'R(h) v = (%.2f, %.2f); v read as world would point to heading %.1f deg' % (
              dx, dy, math.hypot(dx, dy), f0, f1, h, px, py, math.degrees(math.atan2(vx, -vy)) % 360.0))


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
