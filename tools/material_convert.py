"""TR8 Material section (type 10) Xbox360 -> PC converter.

Struct (offsets in section data; Xbox BE, PC LE; verified on 2247 paired material ids):
  0x00 u16,u16 (3, 0xA0)          0x08/0x0C/0x10 ptr -> per-pass VS input lists (pass 0,1,2)
  0x28..0x34 u32 shaderLib id x4  (ResRef type 9)      0x38,0x3C,0x40,0x44,0x48 u32
  0x4C u8[4] render flags: Xbox (b1,b2)=(6,0) -> PC (3,3)  (other values copied)
  0x50 u8[4] (b1 = #textures pass?, b2 = #textures)    0x54 ptr textures, 0x58 u32 #MaterialParams vec4, 0x5C ptr params
  0x60 u32 n, 0x64 ptr; 0x68 u32 n, 0x6C ptr (16-byte records, u32/float)
  0x70 u8[4]   0x74.. u32
  input list @T: u32 0, 0, count, passIndex; count x 28B {u32 semanticHash, i32 -1, u16 a, u16 b, f32/u32 x4}
  params @P: count x vec4 f32 (packing is shader-dependent, see param rules)
  textures @T: n x 16B {u32 textureId (ResRef type 5), u32, u32 type, u8, u8 slot, u16 filter}
Relocations: parse BE / write LE via drm_reloc; ids remapped through callables.
"""
import struct, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_reloc as R

def _sw32(src, out, o): out[o:o + 4] = src[o:o + 4][::-1]
def _sw16x2(src, out, o): out[o:o + 2] = src[o:o + 2][::-1]; out[o + 2:o + 4] = src[o + 2:o + 4][::-1]

def layout(xd, rel):
    """Return dict of region offsets from Xbox data + parsed reloc."""
    ptr = dict(rel.internal)
    L = dict(lists=[ptr.get(o) for o in (0x08, 0x0C, 0x10)], tex=ptr.get(0x54), params=ptr.get(0x5C),
             x60=ptr.get(0x64), x68=ptr.get(0x6C))
    return L

def convert(xd, xreloc, shader_map=None, tex_map=None, param_rule=None, flags_rule=True):
    """xd: Xbox material data; xreloc: Xbox reloc blob. shader_map(xid)->pcid, tex_map(xid)->pcid.
    param_rule: optional callable(list_of_vec4) -> list_of_vec4 (PC packing for the chosen PC shader).
    Returns (pc_data, pc_reloc_blob)."""
    rel = R.parse(xreloc, 'be')
    L = layout(xd, rel)
    out = bytearray(len(xd))
    for o in range(0, len(xd) - 3, 4): _sw32(xd, out, o)
    _sw16x2(xd, out, 0x00)
    out[0x4C:0x50] = xd[0x4C:0x50]
    if flags_rule and xd[0x4D] == 6 and xd[0x4E] == 0: out[0x4D] = 3; out[0x4E] = 3
    out[0x50:0x54] = xd[0x50:0x54]
    out[0x70:0x74] = xd[0x70:0x74]
    for T in L['lists']:
        if T is None: continue
        n = struct.unpack_from('>I', xd, T + 8)[0]
        for k in range(n): _sw16x2(xd, out, T + 16 + 28 * k + 8)
    if L['tex'] is not None:
        idoffs = sorted(o for t, o in rel.idref + rel.idref_a if t == 5)
        for o in idoffs:
            e = o  # texture entry start (id field at +0)
            if e + 16 <= len(xd):
                out[e + 12:e + 14] = xd[e + 12:e + 14]
                out[e + 14:e + 16] = xd[e + 14:e + 16][::-1]
    # id remaps
    for t, o in rel.idref + rel.idref_a:
        xid = struct.unpack_from('>I', xd, o)[0]
        m = shader_map if t == 9 else (tex_map if t == 5 else None)
        if m is not None and xid not in (0, 0xFFFFFFFF):
            struct.pack_into('<I', out, o, m(xid))
    # MaterialParams repacking (changes section size: everything after params shifts)
    if param_rule is not None and L['params'] is not None:
        n = struct.unpack_from('>I', xd, 0x58)[0]
        P = L['params']
        vx = [struct.unpack_from('>4f', xd, P + 16 * i) for i in range(n)]
        vp = param_rule(vx)
        newblk = b''.join(struct.pack('<4f', *v) for v in vp)
        delta = len(newblk) - 16 * n
        end = P + 16 * n
        out = out[:P] + bytearray(newblk) + out[end:]
        struct.pack_into('<I', out, 0x58, len(vp))
        sh = lambda off: off + delta if off >= end else off
        rel.internal = [(sh(a), sh(b)) for a, b in rel.internal]
        rel.idref = [(t, sh(o)) for t, o in rel.idref]
        rel.idref_a = [(t, sh(o)) for t, o in rel.idref_a]
    return bytes(out), R.write(rel, 'le')

# ---------------- MaterialParams repacking rules (learned from base pairs) ----------------
def shader_key(xd):
    return struct.unpack_from('>4I', xd, 0x28)

def read_params(d, rel_blob, e):
    rel = R.parse(rel_blob, 'be' if e == '>' else 'le')
    P = dict(rel.internal).get(0x5C)
    n = struct.unpack_from(e + 'I', d, 0x58)[0]
    return [struct.unpack_from(e + '4f', d, P + 16 * i) for i in range(n)] if P is not None else []

def learn_rule(examples):
    """examples: list of (xbox vec4 list, pc vec4 list) for one shader key. Returns rule = (npc, [src per pc float])
    src = ('x', i) take Xbox float i, or ('c', value) constant. None if inconsistent."""
    npc = {len(p) for _, p in examples}
    if len(npc) != 1: return None
    npc = npc.pop()
    srcs = []
    for j in range(4 * npc):
        cand = None
        for x, p in examples:
            fx = [v for q in x for v in q]; pv = p[j // 4][j % 4]
            c = {i for i, v in enumerate(fx) if v == pv}
            cand = c if cand is None else cand & c
        if cand:
            # prefer a source keeping vec4 component alignment, then lowest index
            best = sorted(cand, key=lambda i: (i % 4 != j % 4, i))[0]
            srcs.append(('x', best))
        else:
            vals = {p[j // 4][j % 4] for _, p in examples}
            if len(vals) != 1: return None
            srcs.append(('c', vals.pop()))
    return (npc, srcs)

def apply_rule(rule, vx):
    npc, srcs = rule
    fx = [v for q in vx for v in q]
    f = [(fx[s[1]] if s[1] < len(fx) else 0.0) if s[0] == 'x' else s[1] for s in srcs]
    return [tuple(f[4 * k:4 * k + 4]) for k in range(npc)]
