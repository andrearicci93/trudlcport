"""Cobweb sheets of dlc_caverns as ALPHA-CUTOUT materials (2026-10-11, alternative to tools/web_occluder_patch.py).

Why the webs hide the adren-trap deck (A/B 2026-10-10: deck appears when the 4 web materials are degenerated):
  web materials 20676/20673/23173/23329 got the surrogate PC tuple 1762/1763/1764/1765 (base 7983 -> PC 16160).
  Its pass-0 PS 1762 (depth / aux pass, permutation 2 writes packed depth) kills ONLY on vertex alpha
  (texkill(v0.w - AlphaThreshold)), never on the web texture alpha -> the whole quad is written in pass 0 ->
  invisible occluder. The Xbox web pass-0 PS 2207 reads AlphaThreshold + the material textures (alpha test).
Fix: give the 4 web materials the PC tuple 240/241/242/243 = the standard PC alpha-tested lit material
  (pass 0/1 = texkill(tex(s3).a * c100.w - AlphaThreshold), colour PS 242 outputs alpha = tex.a * MaterialOpacity),
  already used by DLC materials 20170/20260 in this same DRM and by 100+ base PC materials; the material VS input
  lists are identical to the base users (23173: same set, pass-2 order re-sorted to the base order).
  Per material: tuple, 0x40 = 4213 and 0x50..0x53 = 02 03 03 00 (all base users), texture entries re-laid out like
  base 3741 (type1 diffuse -> s3, type2 -> s2, type3 normal -> s0, type6 -> s4 flag 1, the type-4 cube entry ->
  texture 255 (white, present in the DRM) type 7 flag 2 on s1), MaterialParams (count kept = 7, PS reads 6):
  c100 = (Xbox p1.rgb, 1) diffuse/alpha scale, c101 = (p0.rgb, 0) spec, c102 = 1 (UV scales), c103 = (1,1,1,0),
  c104 = (1,1,1,5), c105 = (0.7,1,0,0) (base 3741 values), c106 = 0.
  x38 (5) / x44 / flags / record @0x68 kept.
  20676/20673 use DXT5 web textures 6754/6745 with real alpha (strands). 23173/23329 use DXT1 6610 (white strands on
  black, alpha 255 everywhere; only these two materials use it in dlc_caverns): 6610 is re-encoded DXT5 with
  alpha = min(255, 2 * luminance), colour unchanged (3-colour DXT1 blocks re-encoded 4-colour).
Only material sections 20676/20673/23173/23329 and texture section 6610 change.
usage: tools/venv/bin/python -I tools/web_cutout.py SRC.drm [SRC2.drm ..] OUT_dir   (streamgroups/ subdir kept)
Texture/material sections are shared by id between resident DRMs: patch EVERY DRM that carries a web material or 6610
(dlc_caverns, dlc_caverns_hall [23173 + 6610; 20264 also samples 6610.a as a lighting/reflection weight -> now
weaker on the black gaps], streamgroups/dlc_water_wheel_waterwheel_main [4 webs + 6610]).
"""
import sys, os, struct, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import drm_write as DW, drm_reloc as R, tex_convert as TC, material_reslot as MR, shader_map as SM

WEBS = (20676, 20673, 23173, 23329)
LUMA_TEX = {6610}
TUPLE = (240, 241, 242, 243)
REF = 3741                          # base PC material with this tuple (VS input order / header bytes)
SLOT = {1: (3, 0), 2: (2, 0), 3: (0, 0), 6: (4, 1), 7: (1, 2)}

def bc4_encode(a):
    """a (N,16) uint8 -> (N,8) BC4 blocks, 8-value mode (a0 > a1) or constant."""
    a = a.astype(np.int32); n = len(a)
    a0 = a.max(1); a1 = a.min(1)
    pal = np.zeros((n, 8), np.int32); pal[:, 0] = a0; pal[:, 1] = a1
    for i in range(1, 7): pal[:, i + 1] = ((7 - i) * a0 + i * a1) // 7
    ix = np.abs(a[:, :, None] - pal[:, None, :]).argmin(2)
    ix = np.where((a0 == a1)[:, None], 0, ix)
    bits = np.zeros(n, np.uint64)
    for k in range(16): bits |= ix[:, k].astype(np.uint64) << np.uint64(3 * k)
    out = np.zeros((n, 8), np.uint8); out[:, 0] = a0; out[:, 1] = a1
    for i in range(6): out[:, 2 + i] = ((bits >> np.uint64(8 * i)) & np.uint64(255)).astype(np.uint8)
    return out

def _to565(rgb):
    rgb = rgb.astype(np.int32)
    return ((rgb[..., 0] >> 3) << 11) | ((rgb[..., 1] >> 2) << 5) | (rgb[..., 2] >> 3)

def bc1_4colour(blk, px):
    """DXT1 blocks -> colour blocks valid in DXT5 (always 4-colour): 4-colour blocks copied, 3-colour ones
    re-encoded from the decoded pixels px (N,16,4) (endpoints = brightest / darkest texel)."""
    out = blk.copy()
    c0 = blk[:, 0].astype(np.int32) | (blk[:, 1].astype(np.int32) << 8)
    c1 = blk[:, 2].astype(np.int32) | (blk[:, 3].astype(np.int32) << 8)
    bad = np.nonzero(c0 <= c1)[0]
    for b in bad:
        p = px[b, :, :3].astype(np.int32); lum = p.sum(1)
        e0, e1 = _to565(p[lum.argmax()]), _to565(p[lum.argmin()])
        if e0 < e1: e0, e1 = e1, e0
        if e0 == e1:
            out[b] = [e0 & 255, e0 >> 8, e1 & 255, e1 >> 8, 0, 0, 0, 0]; continue
        q0, q1 = TC._565(np.array([e0, e1]))
        pal = np.stack([q0, q1, (2 * q0 + q1) // 3, (q0 + 2 * q1) // 3])
        ix = ((p[:, None, :] - pal[None]) ** 2).sum(2).argmin(1)
        bits = int(sum(int(ix[k]) << (2 * k) for k in range(16)))
        out[b] = [e0 & 255, e0 >> 8, e1 & 255, e1 >> 8] + [(bits >> (8 * i)) & 255 for i in range(4)]
    return out, len(bad)

def luma_alpha_dxt5(d):
    h, kind, res = TC.pc_levels(d)
    assert kind == 'DXT1' and len(res) == 1, (kind, len(res))
    body = bytearray(); n3 = 0
    for blk, w, hh in res[0]:
        px = TC.decode_bc1_color(blk)
        lum = (px[:, :, 0].astype(np.int32) * 77 + px[:, :, 1].astype(np.int32) * 150 + px[:, :, 2].astype(np.int32) * 29) >> 8
        alpha = np.minimum(255, 2 * lum).astype(np.uint8)
        cb, k = bc1_4colour(blk, px); n3 += k
        body += np.concatenate([bc4_encode(alpha), cb], 1).astype(np.uint8).tobytes()
    hdr = bytearray(d[:24])
    struct.pack_into('<I', hdr, 4, TC.FOURCC['DXT5']); struct.pack_into('<I', hdr, 8, len(body)); hdr[0x14] = 0
    return bytes(hdr) + bytes(body), n3

def patch_material(d, reloc, ref):
    rd, rr = ref
    out = bytearray(d)
    rel = R.parse(reloc, 'le')
    struct.pack_into('<4I', out, 0x28, *TUPLE)
    struct.pack_into('<I', out, 0x40, struct.unpack_from('<I', rd, 0x40)[0])
    out[0x50:0x54] = rd[0x50:0x54]
    # VS input lists: same set as the reference, order as the reference
    ip = dict(rel.internal); rip = dict(R.parse(rr, 'le').internal)
    for f in (0x08, 0x0C, 0x10):
        T, RT = ip[f], rip[f]
        n = struct.unpack_from('<I', d, T + 8)[0]
        recs = {struct.unpack_from('<I', d, T + 16 + 28 * k)[0]: d[T + 16 + 28 * k:T + 44 + 28 * k] for k in range(n)}
        order = [struct.unpack_from('<I', rd, RT + 16 + 28 * k)[0] for k in range(struct.unpack_from('<I', rd, RT + 8)[0])]
        assert sorted(order) == sorted(recs), 'VS inputs differ from the reference material'
        for k, sem in enumerate(order): out[T + 16 + 28 * k:T + 44 + 28 * k] = recs[sem]
    # textures
    for o, tid, ty, slot in MR.tex_entries(d, rel, '<'):
        if ty == 4:
            struct.pack_into('<III', out, o, 255, 0, 7); ty = 7
        s, fl = SLOT[ty]
        out[o + 12] = fl; out[o + 13] = s
    # params
    n = struct.unpack_from('<I', d, 0x58)[0]; po = ip[0x5C]
    p = [struct.unpack_from('<4f', d, po + 16 * i) for i in range(n)]
    newp = [(p[1][0], p[1][1], p[1][2], 1.0), (p[0][0], p[0][1], p[0][2], 0.0), (1.0, 1.0, 1.0, 1.0), (1.0, 1.0, 1.0, 0.0),
            (1.0, 1.0, 1.0, 5.0), (0.7, 1.0, 0.0, 0.0)] + [(0.0, 0.0, 0.0, 0.0)] * (n - 6)
    for i, v in enumerate(newp): struct.pack_into('<4f', out, po + 16 * i, *v)
    return bytes(out), p, newp

def patch(raw):
    Lb = MR.libs(); ref = Lb['PM'][REF]
    assert struct.unpack_from('<4I', ref[0], 0x28) == TUPLE
    D = DW.read(raw, 'le'); rep = []
    for s in D.sections:
        if s.type == 10 and s.id in WEBS:
            nd, p, newp = patch_material(s.data, s.reloc, ref)
            v1, v2 = SM.vs_inputs(nd, s.reloc, '<'), SM.vs_inputs(*ref, '<')
            assert v1 == v2
            s.data = nd; rep.append(('material', s.id, [tuple(round(x, 3) for x in v) for v in newp[:6]]))
        elif s.type == 5 and s.id in LUMA_TEX:
            s.data, n3 = luma_alpha_dxt5(s.data); rep.append(('texture DXT1->DXT5 luma alpha', s.id, n3))
    return D.write('le'), rep

if __name__ == '__main__':
    out = sys.argv[-1]
    for src in sys.argv[1:-1]:
        raw = DW.cdrm_decode(open(src, 'rb').read(), 'le')
        new, rep = patch(raw)
        print(src)
        for r in rep: print('  ', r)
        A = DW.read(raw, 'le'); B = DW.read(new, 'le')
        print('   changed sections', [(a.type, a.id) for a, b in zip(A.sections, B.sections) if a.data != b.data or a.reloc != b.reloc])
        name = os.path.basename(src)
        sub = os.path.basename(os.path.dirname(os.path.abspath(src)))
        if sub == 'streamgroups': name = os.path.join(sub, name)
        dst = os.path.join(out, name); os.makedirs(os.path.dirname(dst), exist_ok=True)
        data = DW.cdrm_encode(new, 'le'); open(dst, 'wb').write(data); print('   wrote', dst, hashlib.md5(data).hexdigest())
