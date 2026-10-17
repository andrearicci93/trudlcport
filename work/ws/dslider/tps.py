import sys, struct
sys.path.insert(0, '/path/to/trudlcport/tools')
import model_point_fix as M, drm_write as DW, dtp_audit as DA, drm_reloc as R
rel = 'dlc1_uo_dragon_slider.drm'
xs = DA.xsecs(rel)
for p in sys.argv[1:]:
    D = DW.read(open(p, 'rb').read(), 'le'); print(p)
    for x, i in DA.section_pairs(xs, D):
        if x['type'] != 7 or x['data'][:4] != M.MAGIC: continue
        d = D.sections[i].data
        for kind, e, es in M.elements(x['data'], R.parse(x['reloc'], 'be')):
            if kind != 'TP': continue
            pt = d[e:e+32]; xp = x['data'][e:e+32]
            seg, typ = struct.unpack('<HH', pt[:4]); pos = struct.unpack('<3f', pt[4:16]); idv = struct.unpack('<I', pt[28:32])[0]
            print('  DTP', D.sections[i].id, '@0x%x' % e, 'seg', seg, 'TIPO', typ, 'pos', pos, 'id', idv, '| xbox', xp[:4].hex(), xp[28:].hex())
