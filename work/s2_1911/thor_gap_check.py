"""Read-only arithmetic (S2 analysis 2026-11-19): flat gap D between the Thor pillar's top edge and a column ring, for a
pillar centre seen live, with the ring centres / radii and the pillar radius of the R8b finding (live frame).
D = |centre - ring centre| - ring radius - pillar radius; also the side of the ring the pillar faces.

Usage (from the repository root):
  ../bin/pyt -t 60 work/s2_1911/thor_gap_check.py X Y [PILLAR_R] [RING=NAME:CX:CY:R ...]
  default rings: W982 (-13402, 3085, r 402), NE981 (-9423, 4703, r 403); default pillar radius 552
"""
import sys, math


def main(argv):
    x, y = float(argv[0]), float(argv[1])
    pr = float(argv[2]) if len(argv) > 2 and ':' not in argv[2] else 552.0
    rings = [a.split('=', 1)[1] for a in argv if a.startswith('RING=')] or ['W982:-13402:3085:402', 'NE981:-9423:4703:403']
    for r in rings:
        name, cx, cy, rr = r.split(':')
        cx, cy, rr = float(cx), float(cy), float(rr)
        d = math.hypot(x - cx, y - cy)
        ang = math.degrees(math.atan2(y - cy, x - cx))
        side = 'east' if -45 <= ang <= 45 else 'north' if 45 < ang <= 135 else 'south' if -135 <= ang < -45 else 'west'
        print('%s: centre distance %.0f, gap D = %.0f units (%.2f m at 291 u/m), pillar on the %s side of the ring (%.0f deg)'
              % (name, d, d - rr - pr, (d - rr - pr) / 291.0, side, ang))


if __name__ == '__main__':
    main(sys.argv[1:])
