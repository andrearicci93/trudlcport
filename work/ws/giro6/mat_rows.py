"""Giro 6: per un materiale, righe del contratto sampler (registro Xbox -> slot PC) con colore medio texel Xbox vs PC. Uso: mat_rows.py MODS_DIR MAT [DRM]"""
import sys, io, contextlib, struct
import numpy as np
sys.path.insert(0, '/path/to/trudlcport/work/ws/giro5')
with contextlib.redirect_stdout(io.StringIO()):
    import build_unlit as B
import texlib
texlib.set_baseline('B88b_acqua')
F14 = B.F14; C = F14.C
tree = C.read_tree(sys.argv[1]); mid = int(sys.argv[2]); L = B.libs(); DM = L['DM']
for rel, d in sorted(tree.items()):
    if len(sys.argv) > 3 and rel != sys.argv[3]: continue
    for s in d.sections:
        if s.type == 10 and s.id == mid:
            dl = struct.unpack_from('>4I', DM[mid][0], 0x28)[2]; pl = struct.unpack_from('<4I', s.data, 0x28)
            print(rel, 'PC lib', pl, 'Xbox lib', dl)
            sm, rows = F14.derive_slotmap(mid, dl, s.data, s.reloc)
            for r in rows:
                x = texlib.xb_mean(r['xbox_tex']); p = texlib.pc_mean(r['pc_tex'])
                f = lambda m: None if m is None or m['rgba'] is None else (m['kind'], 'cubo' if m['cube'] else '2D', np.round(m['rgba'], 3).tolist())
                print('  reg X%d -> slot PC%d  type %s flag %s  Xbox tex %s %s | PC tex %s %s' % (r['xbox_reg'], r['pc_slot'], r['type'], r['flag'], r['xbox_tex'], f(x), r['pc_tex'], f(p)))
            if len(sys.argv) <= 3: break
