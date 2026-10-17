"""Diagnostic / workaround patch for the invisible adrenaline-trap bridge in dlc_caverns (2026-10-10).

Finding (offline, see NOTES.md 'Invisible adren-trap bridge'): the trap object dlc1_uo_adren_trap (intro 9864 at
(15789,1894,-7585), mesh 20944, material 21118) lies 97% by area (99% of its horizontal deck area) INSIDE a box of
vertical terrain sheets of dlc_caverns: materials 20676/20673/23173/23329 (side planes y~1277 / y~2450-2570, end caps
x~15300 / x~19700, z -8443..-6292). Their textures (6754/6745 colour, alpha < 32 on 95-97%) are COBWEBS: on Xbox they
are alpha-cut strands; on PC they got the water-like surrogate tuple 1762-1765 (base material 7983 -> PC 16160) whose
pass-0/colour shaders do not cut on the web texture alpha -> the whole quad is drawn almost transparent and can act as
an invisible occluder for objects drawn after the terrain (the trap), while terrain behind it stays visible.
The mesh/material/model/object-root data of the trap itself check out against the Xbox source and base-PC word classes.

Patch: every triangle of those web materials whose centroid lies in the trap box (+margin) becomes degenerate
(i0,i0,i0) in the terrain index buffer.  Only index-buffer bytes change: section sizes, relocations, draw lists and all
other sections are byte-identical.  Webs elsewhere in the level are untouched.

usage: tools/venv/bin/python -I tools/web_occluder_patch.py SRC_dlc_caverns.drm OUT_dir [--all]   (--all: every web tri)
"""
import sys, os, struct, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import drm_write as DW, drm_reloc as R, terrain_convert as TC

WEB_MATS = {20676, 20673, 23173, 23329}
# trap world box (mesh 20944 bbox placed at intro 9864, rotation 0) + margin
TRAP_LO = np.array([14298.0, 1276.0, -7807.0]) - 500
TRAP_HI = np.array([19939.0, 2526.0, -6203.0]) + 500
POS = 0xD2F7D823

def patch(raw_le, all_webs=False):
    D = DW.read(raw_le, 'le')
    rep = collections.Counter()
    for s in D.sections:
        if s.type != 12 or not TC.is_terrain(s.data): continue
        d = bytearray(s.data); T = TC.parse(d, '<'); H = T['H']
        rel = R.parse(s.reloc, 'le'); ip = dict(rel.internal)
        ml = ip.get(0x0C)
        nm = struct.unpack_from('<I', d, ml)[0]; mats = struct.unpack_from('<%dI' % nm, d, ml + 4)
        io = H + T['offIdx']
        idx = np.frombuffer(bytes(d), dtype='<u2', count=T['nIdx'], offset=io).copy()
        VB = []
        for voff, _z, nv, vfi in T['vbs']:
            vf = T['vfs'][vfi]; st = vf['stride']; pe = [e for e in vf['elems'] if e[0] == POS][0]
            assert pe[2] == 2, 'non-float position'
            raw = np.frombuffer(bytes(d), np.uint8, count=nv * st, offset=H + voff).reshape(nv, st)
            VB.append(raw[:, pe[1]:pe[1] + 12].copy().view('<f4').reshape(nv, 3))
        owner = {}
        changed = False
        for slot, seq, L in TC.draw_lists(d, T, '<'):
            for yi, ic, ist in L:
                Y = T['Y'][yi]; mid = mats[Y[0]] if Y[0] < len(mats) else None
                assert ic % 3 == 0
                key = (ist, ic)
                if key in owner and owner[key] != yi: raise ValueError('index range shared by two batches')
                owner[key] = yi
                if mid not in WEB_MATS: continue
                pos = VB[Y[1]]
                for t in range(ist, ist + ic, 3):
                    tri = idx[t:t + 3]
                    if tri[0] == tri[1] == tri[2]: continue
                    c = pos[tri].mean(0)
                    if all_webs or (np.all(c > TRAP_LO) and np.all(c < TRAP_HI)):
                        idx[t + 1] = idx[t]; idx[t + 2] = idx[t]
                        rep[mid] += 1; changed = True
        if changed:
            d[io:io + 2 * T['nIdx']] = idx.astype('<u2').tobytes()
            assert len(d) == len(s.data)
            s.data = bytes(d)
    return D.write('le'), rep

if __name__ == '__main__':
    src, out = sys.argv[1], sys.argv[2]
    raw = DW.cdrm_decode(open(src, 'rb').read(), 'le')
    new, rep = patch(raw, '--all' in sys.argv)
    os.makedirs(out, exist_ok=True)
    A = DW.read(raw, 'le'); B = DW.read(new, 'le')
    diff = [(a.type, a.id) for a, b in zip(A.sections, B.sections) if a.data != b.data or a.reloc != b.reloc]
    assert all(t == 12 for t, _ in diff) and len(A.sections) == len(B.sections)
    dst = os.path.join(out, os.path.basename(src))
    open(dst, 'wb').write(DW.cdrm_encode(new, 'le'))
    print('degenerated web triangles per material', dict(rep), 'sections changed', diff, '->', dst)
