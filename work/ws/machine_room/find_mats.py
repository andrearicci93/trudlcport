"""find_mats.py - (20/11/2026) solo lettura. Cerca nel dump matrici 4x4 (righe, traslazione a [12..14], [15]=1) con parte 3x3
ortonormale e traslazione vicina a una posizione data (x,y entro R, z entro [zmin,zmax]). uso: find_mats.py DUMP x y R zmin zmax"""
import sys, struct, mmap
import numpy as np
sys.path.insert(0, '/path/to/trudlcport/tools')
from minidump_read import Minidump
D, X, Y, Rr, Z0, Z1 = sys.argv[1], *map(float, sys.argv[2:7])
m = Minidump(D); f = open(D, 'rb'); mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
out = []
for va, sz, fo in m.ranges:
    if sz < 64: continue
    a = np.frombuffer(mm, dtype='<f4', count=sz // 4, offset=fo)
    with np.errstate(all='ignore'):
        cand = np.nonzero((np.abs(a[:-3] - X) < Rr) & (np.abs(a[1:-2] - Y) < Rr) & (a[2:-1] > Z0) & (a[2:-1] < Z1) & (a[3:] == 1.0))[0]
    for k in cand:
        if k < 12: continue
        M = a[k - 12:k + 4].reshape(4, 4)
        R = M[:3, :3].astype(np.float64)
        if not np.all(np.isfinite(R)): continue
        if np.abs(R @ R.T - np.eye(3)).max() > 0.02 or abs(M[0, 3]) > 1e-3 or abs(M[1, 3]) > 1e-3 or abs(M[2, 3]) > 1e-3: continue
        out.append((va + 4 * (k - 12), M))
for addr, M in out:
    yaw = np.degrees(np.arctan2(M[0, 1], M[0, 0]))
    print('%08x t=(%.1f %.1f %.1f) yaw=%.2f row0=(%.3f %.3f %.3f) row2=(%.3f %.3f %.3f)' % (addr, *M[3, :3], yaw, *M[0, :3], *M[2, :3]))
print('totale', len(out))
