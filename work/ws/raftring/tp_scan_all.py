"""tp_scan_all.py - elenca per ogni file del set i TP con TIPO&4 (grapple) o &8/&0x40, Xbox vs PC."""
import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
import model_point_fix as M, dtp_audit as DA, drm_write as DW, drm_reloc as R
sd = sys.argv[1]
for rel, path in sorted(DA.overlay([sd], None).items()):
    xs = DA.xsecs(rel)
    if xs is None: continue
    try: D = DW.read(open(path, 'rb').read(), 'le')
    except Exception as e: continue
    for x, i in DA.section_pairs(xs, D):
        sec = D.sections[i]
        if x['type'] != 7 or x['data'][:4] != M.MAGIC: continue
        xd, pd = x['data'], sec.data
        for k, e, es in M.elements(xd, R.parse(x['reloc'], 'be')):
            if k != 'TP': continue
            xty = struct.unpack_from('>H', xd, e + 2)[0]; pty = struct.unpack_from('<H', pd, e + 2)[0]
            if (xty | pty) & 0x4c:
                xp = struct.unpack_from('>3f', xd, e + 4); pp = struct.unpack_from('<3f', pd, e + 4)
                print('%s sec %d @0x%x X TIPO 0x%x (%.1f,%.1f,%.1f) | PC TIPO 0x%x (%.1f,%.1f,%.1f) %s' % (rel, sec.id, e, xty, *xp, pty, *pp, 'OK' if xty == pty else '<<< DIFF'))
