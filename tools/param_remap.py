"""MaterialParams RE-PACKING for DLC materials whose pixel shaders were replaced by a PC surrogate compiled from the
same shader graph but with ANOTHER constant packing (2026-10-11, 'yellow-gold adren-trap bridge').

Finding: dlc1_uo_adren_trap deck material 21118 uses DLC PS libs 2298/2299 (class C2/C1) -> PC 2037/2038, the PC
build of base Xbox 1200/1201 (base pair 12551 -> PC 20056: params identical = 1201 packing is the PC packing).
2299 and 1201 have the SAME samplers (names and registers) and the same instruction stream (Xenos microcode
aligned 507/552), but the DLC compiler packed MaterialParams (c100..c116) differently. material_dlc copied the 17
vec4 1:1, so e.g. PC c112.zw (two colour-term weights, 1/1 in base) got the DLC spec-power pair (6, 23) and PC
c100/c101 (lerp base / diffuse tint) got swapped -> saturated over-bright 'gold' planks.
Map derived by hand from the microcode (tools: scratch xdis/fdec, documented in NOTES.md):
  UV scales by sampler register (tfetch const index), colour terms by aligned instruction (mul/add/mad with the
  same operands), scalars of mul_const_* (constant component = 4th swizzle letter) by aligned instruction.
  Cross-check: the re-packed 21118 has the base layout pattern of 12551 (c112 = 2,2,1,1, c113.w = 0.7, ...).
  Pass-1 PS 2298 vs 1200 uses the same map (c112.xy/c111.zw, c109.zw/c109.xy, c116.z/c113.z, c113.x/c112.w,
  c100.w/c101.w) -> consistent.
  Not 1:1: PC c116.y (per-light scalar, 'k * gloss') vs DLC c112.z + (c112.w - c112.z) * gloss -> c116.y := c112.w.

usage: tools/venv/bin/python -I tools/param_remap.py OUT_DIR SRC.drm [SRC2.drm ..]   (writes only changed files)
"""
import sys, os, struct, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_write as DW, drm_reloc as R

# PC (B) component <- DLC Xbox (A) component, registers relative to c100; ('k', v) = constant value
X, Y, Z, W = 0, 1, 2, 3
def _v(r, *cs): return [(r, c) for c in cs]
MAP_2299_TO_1201 = {
    0: _v(1, X, Y, Z, W), 1: _v(0, X, Y, Z, W), 2: _v(3, X, Y, Z, W), 3: _v(2, X, Y, Z, W),
    4: _v(4, X, Y, Z, W), 5: _v(5, X, Y, Z, W), 6: _v(6, X, Y, Z, W), 7: _v(7, X, Y, Z, W),
    8: [(9, X), (9, Y), (8, Z), (8, W)],
    9: [(9, Z), (9, W), (8, X), (8, Y)],
    10: [(10, Z), (10, W), (11, X), (11, Y)],
    11: [(11, Z), (11, W), (12, X), (12, Y)],
    12: [(10, X), (10, Y), (13, Y), (13, X)],
    13: [(13, Z), (13, W), (16, Z), (14, X)],
    14: [(14, Y), (14, Z), (14, W), (15, X)],
    15: [(15, Y), (15, Z), (15, W), (16, X)],
    16: [(16, Y), (12, W), ('k', 1.0), ('k', 0.0)],
}
# Xbox DLC material id -> (expected PC tuple, map)
MATERIALS = {21118: ((0, 2037, 2038, 264), MAP_2299_TO_1201)}

def remap(vx, table):
    out = []
    for b in range(len(vx)):
        out.append(tuple(float(s[1]) if s[0] == 'k' else vx[s[0]][s[1]] for s in table[b]))
    return out

def patch_material(d, reloc, mid):
    tup, table = MATERIALS[mid]
    if struct.unpack_from('<4I', d, 0x28) != tup: raise ValueError('material %d: unexpected PC tuple' % mid)
    ip = dict(R.parse(reloc, 'le').internal)
    n = struct.unpack_from('<I', d, 0x58)[0]; po = ip[0x5C]
    if n != len(table): raise ValueError('material %d: %d params, map has %d' % (mid, n, len(table)))
    vx = [struct.unpack_from('<4f', d, po + 16 * i) for i in range(n)]
    vp = remap(vx, table)
    out = bytearray(d)
    for i, v in enumerate(vp): struct.pack_into('<4f', out, po + 16 * i, *v)
    return bytes(out), vx, vp

def patch_drm(raw):
    D = DW.read(raw, 'le'); rep = []
    for s in D.sections:
        if s.type == 10 and s.id in MATERIALS:
            nd, vx, vp = patch_material(s.data, s.reloc, s.id)
            if nd != s.data: s.data = nd; rep.append((s.id, vx, vp))
    return (D.write('le') if rep else None), rep

if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    for src in sys.argv[2:]:
        new, rep = patch_drm(open(src, 'rb').read())
        for mid, vx, vp in rep:
            print(os.path.basename(src), 'material', mid)
            for i, (a, b) in enumerate(zip(vx, vp)):
                print('  c%d  %-28s -> %s' % (100 + i, ','.join('%g' % round(x, 3) for x in a), ','.join('%g' % round(x, 3) for x in b)))
        if new is not None:
            data = DW.cdrm_encode(new, 'le'); dst = os.path.join(out, os.path.basename(src))
            open(dst, 'wb').write(data); print('  wrote', dst, hashlib.md5(data).hexdigest())
