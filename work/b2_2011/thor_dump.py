"""B2 helper (read-only, 2026-11-20): input file for the offline Thor self-test (src/asi/TruMenu/selftest/
TruThorCoreTest.cpp, TruMenu 0.22.68 B2 point 1). Writes the unit's TerrainGroup collision faces (world frame = mesh
position + vertex, as work/a3_2011/reach_map.py reads them), the markup ledges of R8b's markup_full.py output (live
frame), the artifacts and trigger volumes of the unit's intro list (live = data - origin, ENGINE 9 R8b) and the two
proven pillar spots of 2026-11-18 / 19 (A3 cross-check) as text lines:
  P floor <z> start <x> <y> box <x0> <x1> <y0> <y1>
  F x y z x y z x y z
  L <id> <closed 0/1> <n> x y z ...
  A <intro> x y z          (ma_rw_artifact, sorted by intro: first = A)
  T <intro> x y z          (names with 'trigger')
  Q <name> x y <exit|artA|artB>
The output is game data: write it to <workspace>/local_results/, never into the repository.

Usage (from the repository root):
  ../bin/pyt -t 600 work/b2_2011/thor_dump.py UNIT.drm MARKUP_FULL.txt INTROS.txt OUT.txt
"""
import sys, os, struct
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
import collision_faces as CF


def main(argv):
    if len(argv) != 4:
        print(__doc__)
        return 2
    drm, markup, intros, out = argv
    D, rel = CF.load(drm)
    lines = ['P floor 173.1 start -9113 191 box -16000 -5000 -3600 5800']
    nf = 0
    bad = 0
    for gi, gid, ms, mo, h in CF.meshes(D, rel):
        vs, vo = h['v']; fs, fo = h['f']
        vd = D.sections[vs].data; fd = D.sections[fs].data + b'\0' * 4
        px, py, pz = h['pos']
        V = [struct.unpack_from('<3f', vd, vo + 16 * k) for k in range(h['nv'])]
        for k in range(h['nf']):
            i0, i1, i2, fl = struct.unpack_from('<4I', fd, fo + 20 * k)
            if max(i0, i1, i2) >= len(V):
                bad += 1
                continue
            row = []
            for i in (i0, i1, i2):
                row += ['%.9g' % (V[i][0] + px), '%.9g' % (V[i][1] + py), '%.9g' % (V[i][2] + pz)]
            lines.append('F ' + ' '.join(row))
            nf += 1
    origin = None
    nl = 0
    cur = None
    for line in open(markup).read().splitlines():
        if line.startswith('# origin'):
            origin = [float(v) for v in line.split(';')[0].split()[2:5]]
        elif line.startswith('item'):
            p = line.split()
            cur = (int(p[3]), 1 if p[5] == 'closed' else 0)
        elif line.strip().startswith('pts') and cur:
            pts = line.strip()[3:].replace('(', ' ').replace(')', ' ').split()
            n = len(pts) // 3
            lines.append('L %d %d %d %s' % (cur[0], cur[1], n, ' '.join(pts)))
            nl += 1
            cur = None
    if origin is None:
        print('no origin line in %s' % markup)
        return 1
    arts, trig = [], []
    for line in open(intros).read().splitlines():
        if line.startswith('#') or not line.strip():
            continue
        p = line.split()
        intro, name = int(p[0]), p[5]             # '<intro> idx <i> obj <id> <name> pos <x> <y> <z> ...'
        x, y, z = float(p[7]), float(p[8]), float(p[9])
        live = (x - origin[0], y - origin[1], z - origin[2])
        if 'ma_rw_artifact' in name:
            arts.append((intro, live))
        elif 'trigger' in name:
            trig.append((intro, live))
    for intro, (x, y, z) in sorted(arts):
        lines.append('A %d %.1f %.1f %.1f' % (intro, x, y, z))
    for intro, (x, y, z) in trig:
        lines.append('T %d %.1f %.1f %.1f' % (intro, x, y, z))
    lines.append('Q EXIT -11986 2484 exit')
    lines.append('Q ART -10625 3940 artA')
    with open(out, 'w') as fh:
        fh.write('\n'.join(lines) + '\n')
    print('%s: %d faces (%d with bad indices skipped), %d ledges, %d artifacts, %d triggers, origin %s -> %s' % (
        os.path.basename(drm), nf, bad, nl, len(arts), len(trig), origin, out))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
