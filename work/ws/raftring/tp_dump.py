"""tp_dump.py - TP (target/markup points) Xbox(BE) vs PC(LE) dei modelli di un file DLC. Uso: python -I work/ws/raftring/tp_dump.py <setdir relativo a work> <file.drm>"""
import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
import model_point_fix as M, dtp_audit as DA, drm_write as DW, drm_reloc as R
W = M.W
sd, name = sys.argv[1], sys.argv[2]
files = DA.overlay([sd], {name})
for rel, path in sorted(files.items()):
    xs = DA.xsecs(rel)
    if xs is None: print('no xbox source', rel); continue
    D = DW.read(open(path, 'rb').read(), 'le')
    for x, i in DA.section_pairs(xs, D):
        sec = D.sections[i]
        if x['type'] != 7 or x['data'][:4] != M.MAGIC: continue
        xd, pd = x['data'], sec.data
        rel_ = R.parse(x['reloc'], 'be')
        tps = [(e, es) for k, e, es in M.elements(xd, rel_) if k == 'TP']
        n = struct.unpack_from('>I', xd, 0x5c)[0]
        print('PC sec %d (xbox %d) len %d nTP(hdr) %d provable %d' % (sec.id, x['id'], len(xd), n, len(tps)))
        for e, es in tps:
            xseg, xty = struct.unpack_from('>HH', xd, e); xp = struct.unpack_from('>6f', xd, e + 4); xid = struct.unpack_from('>I', xd, e + 0x1c)[0]
            pseg, pty = struct.unpack_from('<HH', pd, e); pp = struct.unpack_from('<6f', pd, e + 4); pid = struct.unpack_from('<I', pd, e + 0x1c)[0]
            ok = (xseg, xty) == (pseg, pty) and all(abs(a - b) < 1e-4 for a, b in zip(xp, pp))
            print('  @0x%x X seg%d TIPO 0x%x pos(%.2f,%.2f,%.2f) id %d | PC seg%d TIPO 0x%x pos(%.2f,%.2f,%.2f) id %d %s' % (e, xseg, xty, *xp[:3], xid, pseg, pty, *pp[:3], pid, 'OK' if ok else '<<< DIFF'))
