"""Read-only: print chosen activity parameters of chart records, resolving type-41 values (pointer to a variant
{u32 kind, value}: kind 1 / 2 int, 3 / 4 float, 5 bool; reader 0x783680 case 3 -> 0x781ee0) (R2 fall damage).

Usage (from the repository root):
  ../bin/pyt -t 300 work/r2_1811/chart_params.py DRM ENDIAN SID REC[,REC..] PARAM[,PARAM..]
"""
import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import chart_state_path as CP


def main(argv):
    path, e, sid = argv[0], argv[1], int(argv[2])
    recs = [int(x) for x in argv[3].split(',')]
    want = set(int(x) for x in argv[4].split(','))
    C = CP.Chart(path, e, sid)
    f = C.f
    for k in recs:
        r, sid_, hdr, p14, p18, p1c, p20 = C.recs[k]
        r_, hdr_, acts, sids, tr, l20 = C.state(k)
        out = []
        for j, (i, ty, v) in enumerate(acts):
            if i not in want: continue
            o = p14 + 8 * j + 4
            if o in C.it:
                t = C.it[o]
                kind = struct.unpack_from(f + 'I', C.d, t)[0]
                raw = C.d[t + 4:t + 8]
                val = struct.unpack(f + 'f', raw)[0] if kind in (3, 4) else struct.unpack(f + 'i', raw)[0]
                out.append('%d/t%d -> +0x%x {kind %d, %r}' % (i, ty, t, kind, val))
            else:
                out.append('%d/t%d = %s (f %r)' % (i, ty, v.hex(), struct.unpack(f + 'f', v)[0]))
        print('rec #%d sids %s: %s' % (k, sids, '; '.join(out) if out else '-'))


if __name__ == '__main__':
    main(sys.argv[1:])
