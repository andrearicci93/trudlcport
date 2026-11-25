"""column_rays.py - (20/11/2026) solo lettura. Raggi lungo -y (dalla parte di Lara) attraverso il varco della struttura centrale
(mondo x -3036..-1757, z -13640..-12066, piano di collisione y 4824,5) contro le mesh 25552/25553/25554 di dlc2_uo_machine_column
(istanza a (-2363, 1052.2, -22119.6), ossa in posa identita'): primo triangolo colpito per mesh/batch/gruppo/materiale."""
import sys, struct, collections
import numpy as np
sys.path.insert(0, '/path/to/trudlcport/tools')
import drm_write as DW, mesh_tr8 as M
O = np.array([-2363.0, 1052.2, -22119.6])
P = DW.read(open('/path/to/trudlcport/work/baseline/B279_unitcurve/mods/dlc2_uo_machine_column.drm', 'rb').read(), 'le')
xs = np.linspace(-3000, -1800, 13); zs = np.linspace(-13600, -12100, 13)
for mid in (25552, 25553, 25554):
    s = [s for s in P.sections if s.type == 12 and s.id == mid][0]; m = M.Mesh(bytes(s.data), 'le'); d = m.d; idx = np.array(m.indices(), dtype=np.int64)
    hits = collections.Counter(); ymin = []
    for bi, b in enumerate(m.meshes):
        st = b['vf']['stride']; base = 0x10 + b['vdataOff']
        V = np.array([struct.unpack_from('<3f', d, base + v * st) for v in range(b['numVerts'])]) + O
        SK = np.array([d[base + v * st + 20] for v in range(b['numVerts'])])
        for gi, g in enumerate(m.groups):
            pass
        # gruppi di questo batch: quelli con baseIndex dentro il range del batch
        gs = [g for g in m.groups if b['baseIndex'] <= g['baseIndex'] < b['baseIndex'] + 3 * b['numTris']] or [dict(baseIndex=b['baseIndex'], numTris=b['numTris'], material=-1)]
        for g in gs:
            tri = idx[g['baseIndex']:g['baseIndex'] + 3 * g['numTris']].reshape(-1, 3)
            if tri.size == 0 or tri.max() >= len(V): continue
            A, B, Cc = V[tri[:, 0]], V[tri[:, 1]], V[tri[:, 2]]
            for x in xs:
                for z in zs:
                    # intersezione con raggio parallelo a y: baricentriche in (x,z)
                    v0 = Cc[:, [0, 2]] - A[:, [0, 2]]; v1 = B[:, [0, 2]] - A[:, [0, 2]]; v2 = np.array([x, z]) - A[:, [0, 2]]
                    d00 = (v0 * v0).sum(1); d01 = (v0 * v1).sum(1); d11 = (v1 * v1).sum(1); d20 = (v2 * v0).sum(1); d21 = (v2 * v1).sum(1)
                    den = d00 * d11 - d01 * d01; ok = np.abs(den) > 1e-9
                    u = np.where(ok, (d11 * d20 - d01 * d21) / np.where(ok, den, 1), -1); v = np.where(ok, (d00 * d21 - d01 * d20) / np.where(ok, den, 1), -1)
                    inside = (u >= 0) & (v >= 0) & (u + v <= 1)
                    if not inside.any(): continue
                    yy = (A[:, 1] + u * (Cc[:, 1] - A[:, 1]) + v * (B[:, 1] - A[:, 1]))[inside]
                    yy = yy[(yy > 3500) & (yy < 9000)]
                    if yy.size: hits[(bi, g.get('material'))] += 1; ymin.append(yy.max())
    print('mesh', mid, 'raggi colpiti per (batch, materiale):', dict(hits), 'y piu vicina a Lara: %s' % (round(max(ymin)) if ymin else None))
