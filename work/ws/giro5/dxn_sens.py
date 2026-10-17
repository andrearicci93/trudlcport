import sys, io, contextlib, struct
import numpy as np
sys.path.insert(0, '/path/to/trudlcport/work/ws/giro5')
with contextlib.redirect_stdout(io.StringIO()):
    import hall_lit as H
B = H.B; F14 = H.F14; F9 = H.F9; F10 = H.F10; C = H.C; sm3asm = H.sm3asm; texlib = H.texlib
mid, rel, xreg = 20323, 'co_dlc_knight_thrall.drm', 8
L = B.libs(); D, DM = L['D'], L['DM']
tree = C.read_tree(B.ROOT + '/work/baseline/B87_materiali19/mods'); secs = {(s.type, s.id): s for s in tree[rel].sections}
ms = secs[(10, mid)]; dl = struct.unpack_from('>4I', DM[mid][0], 0x28)[2]; pcl = struct.unpack_from('<4I', ms.data, 0x28)[2]
slotmap, rows = F14.derive_slotmap(mid, dl, ms.data, ms.reloc); PPm = F10.params(ms, 'le'); pmap = H.texmap(rows, True)
fl = C.frame_lib(secs[(9, pcl)].data); slot = slotmap[xreg]
print('slot PC del sampler DXN:', slot, 'texel PC medio:', np.round(pmap[slot], 3))
for k, off in enumerate(fl['slots'][:2]):
    prog = sm3asm.decode(fl['entries'][off]['bc']); out = []
    for gy in (1.0, 0.5, 0.0):
        for ay in (0.5, 0.2, 0.9):
            m = dict(pmap); t = np.array(pmap[slot], float); t[1] = gy; t[3] = ay; m[slot] = t
            c = H.color(prog, H.make_env(5, PPm, True), m, F9.ALLB); out.append((gy, ay, np.round(c[:, :3].mean(0), 4).tolist()))
    print('var', k, 'sensibilita (G,A del texel DXN) ->', out)
