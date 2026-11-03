"""Xbox 360 (Xenos) texture section -> PC (PCD9) texture section converter for TRU (cdcEngine TR8).

Section data layouts (the DRM section payload, i.e. after relocations):

Xbox (big-endian), 24-byte header + GPU data
  0x00 char[4] 'X360'
  0x04 u32  D3DFORMAT (Xbox 360 D3DFMT: low 6 bits GPUTEXTUREFORMAT, bit 8 tiled, bits 6-7 endian)
            seen: 0x1A200152 DXT1, 0x1A200153 DXT3, 0x1A200154 DXT5, 0x1A200171 DXN, 0x18280186 A8R8G8B8
  0x08 u32  class/flags (top nibble 0..0xE, no PC equivalent; dropped)
  0x0C u32  0
  0x10 u16  width, 0x12 u16 height
  0x14 u8   bpp-ish (32 for A8R8G8B8, else 0)  == PC byte 0x14
  0x15 u8   mip count beyond base (levels-1)   == PC byte 0x15
  0x16 u16  flags (0x0003 / 0x0000 / 0x8003 = cubemap / 0x0001) == PC flags
  0x18 data: base level then mip levels, Xenos 2D tiled (32x32-block tiles), each level padded to whole
       tiles, levels with min(w,h) <= 16 texels packed together in one "mip tail" tile.
       Cubemaps: per level, 6 faces consecutive (each face padded to whole tiles), see layout().
       Packed tail only when the texture has mips; packed-mip offsets = Xenia GetPackedMipOffset.

PC (little-endian, PCD9), 24-byte header + linear D3D data
  0x00 char[4] 'PCD9'
  0x04 u32  format: FourCC 'DXT1'/'DXT3'/'DXT5' or D3DFMT 0x15 (A8R8G8B8)
  0x08 u32  texture data size (== section size - 24)
  0x0C u32  palette size (0)
  0x10 u16  width, u16 height
  0x14 u8   32 if A8R8G8B8 else 0
  0x15 u8   mips (levels-1)
  0x16 u16  flags
  0x18 data: level-major (cubemap: for each level, faces 0..5); compressed levels are
       max(1,w/4)*max(1,h/4) blocks; A8R8G8B8 is BGRA bytes.
Xenos DXN (BC5) normal maps become DXT5 on PC with R = DXN ch0, G = 255, B = 0, A = DXN ch1
(the DXN ch1 BC4 block is copied verbatim as the DXT5 alpha block; colour block re-encoded).
"""
import struct, sys
import numpy as np

XHDR = struct.Struct('>4sIIIHHBBH')
PHDR = struct.Struct('<4sIIIHHBBH')
FOURCC = {'DXT1': 0x31545844, 'DXT3': 0x33545844, 'DXT5': 0x35545844}
D3DFMT_A8R8G8B8 = 0x15

# Xenos GPUTEXTUREFORMAT -> (name, block dim, bytes per block)
XFMT = {
    0x02: ('8', 1, 1), 0x04: ('1_5_5_5', 1, 2), 0x05: ('5_6_5', 1, 2), 0x06: ('8_8_8_8', 1, 4),
    0x07: ('2_10_10_10', 1, 4), 0x0F: ('4_4_4_4', 1, 2), 0x12: ('DXT1', 4, 8), 0x13: ('DXT2_3', 4, 16),
    0x14: ('DXT4_5', 4, 16), 0x31: ('DXN', 4, 16), 0x3A: ('DXT3A', 4, 8), 0x3B: ('DXT5A', 4, 8),
    0x3C: ('CTX1', 4, 8), 0x0A: ('8_8', 1, 2), 0x18: ('16_16', 1, 4), 0x20: ('32_FLOAT', 1, 4),
    0x1A: ('16_16_16_16', 1, 8), 0x1F: ('16_16_16_16_FLOAT', 1, 8), 0x1E: ('16_16_FLOAT', 1, 4),
}
# Xbox fmt name -> PC format code
PCFMT = {'DXT1': FOURCC['DXT1'], 'DXT2_3': FOURCC['DXT3'], 'DXT4_5': FOURCC['DXT5'], 'DXN': FOURCC['DXT5'],
         '8_8_8_8': D3DFMT_A8R8G8B8}


def parse_xbox(d):
    magic, fmt, u0, u1, w, h, bpp, mips, flags = XHDR.unpack_from(d, 0)
    gpu = fmt & 0x3F
    return dict(magic=magic, d3dfmt=fmt, gpufmt=gpu, tiled=bool(fmt & 0x100), endian=(fmt >> 6) & 3,
                u0=u0, u1=u1, w=w, h=h, bpp=bpp, mips=mips, flags=flags,
                fmtname=XFMT.get(gpu, ('?%02x' % gpu,))[0])


def parse_pc(d):
    magic, fmt, size, pal, w, h, depth, mips, flags = PHDR.unpack_from(d, 0)
    return dict(magic=magic, fmt=fmt, size=size, pal=pal, w=w, h=h, depth=depth, mips=mips, flags=flags)


def log2_ceil(v):
    return max(0, (int(v) - 1).bit_length())


def a32(v):
    return (v + 31) & ~31


# ---------------------------------------------------------------- Xenos tiling
def tiled_index(x, y, aw, bpb):
    """XGAddress2DTiledOffset: block coords -> block index in a tiled surface of pitch aw (mult of 32)."""
    lb = {1: 0, 2: 1, 4: 2, 8: 3, 16: 4}[bpb]
    macro = ((x >> 5) + (y >> 5) * (aw >> 5)) << (lb + 7)
    micro = ((x & 7) + ((y & 6) << 2)) << lb
    off = macro + ((micro & ~15) << 1) + (micro & 15) + ((y & 8) << (3 + lb)) + ((y & 1) << 4)
    return (((off & ~511) << 3) + ((off & 448) << 2) + (off & 63) + ((y & 16) << 7) +
            (((((y & 8) >> 2) + (x >> 3)) & 3) << 6)) >> lb


def packed_offset(W, H, lvl):
    """Texel offset of mip `lvl` inside the packed mip-tail tile (Xenia GetPackedMipOffset)."""
    lw, lh = log2_ceil(W), log2_ceil(H)
    base = max(0, min(lw, lh) - 4)
    pm = lvl - base
    if pm < 3:
        return (0, 16 >> pm) if lw > lh else (16 >> pm, 0)
    if lw > lh:
        return ((1 << (lw - base)) >> (pm - 2), 0)
    return (0, (1 << (lh - base)) >> (pm - 2))


def layout(W, H, levels, bdim, bpb, faces=1):
    """Return list per level of (list per face of (grid_off_blocks, aw, ah, ox, oy), wb, hb) and total blocks."""
    off = 0
    out = []
    tail = None  # (grid offsets per face, aw, ah)
    align = max(1, 4096 // bpb)  # 4 KiB alignment in blocks
    for l in range(levels):
        w, h = max(1, W >> l), max(1, H >> l)
        wb, hb = (w + bdim - 1) // bdim, (h + bdim - 1) // bdim
        packed = levels > 1 and min(log2_ceil(w), log2_ceil(h)) <= 4
        if packed and tail is None:
            aw, ah = a32(wb), a32(hb)
            fo = []
            for f in range(faces):
                fo.append(off); off += (aw * ah + align - 1) // align * align
            tail = (fo, aw, ah)
        if packed:
            fo, aw, ah = tail
            tx, ty = packed_offset(W, H, l)
            out.append(([(g, aw, ah, tx // bdim, ty // bdim) for g in fo], wb, hb))
        else:
            aw, ah = a32(wb), a32(hb)
            fl = []
            for f in range(faces):
                fl.append((off, aw, ah, 0, 0)); off += (aw * ah + align - 1) // align * align
            out.append((fl, wb, hb))
    return out, off


_idx_cache = {}


def untile_level(blocks, g, wb, hb, bpb):
    goff, aw, ah, ox, oy = g
    key = (aw, wb, hb, ox, oy, bpb)
    idx = _idx_cache.get(key)
    if idx is None:
        yy, xx = np.mgrid[0:hb, 0:wb]
        idx = tiled_index((xx + ox).ravel(), (yy + oy).ravel(), aw, bpb)
        _idx_cache[key] = idx
    i = idx + goff
    if i.max() >= len(blocks):
        raise ValueError('tiled index out of range')
    return blocks[i]


def swap_endian(raw, endian):
    a = np.frombuffer(raw, np.uint8)
    if endian == 1: return a.reshape(-1, 2)[:, ::-1].ravel()
    if endian == 2: return a.reshape(-1, 4)[:, ::-1].ravel()
    if endian == 3: return a.reshape(-1, 2, 2)[:, ::-1, :].ravel()
    return a


def xbox_levels(d):
    """Decode Xbox texture section -> (hdr, [face][level] -> np.array (hb*wb, bpb) linear blocks)."""
    h = parse_xbox(d)
    name, bdim, bpb = XFMT[h['gpufmt']]
    faces = 6 if h['flags'] & 0x8000 else 1
    levels = h['mips'] + 1
    blocks = swap_endian(d[24:], h['endian'])
    blocks = blocks[:len(blocks) // bpb * bpb].reshape(-1, bpb)
    lay, total = layout(h['w'], h['h'], levels, bdim, bpb, faces)
    res = [[None] * levels for _ in range(faces)]
    for l, (gl, wb, hb) in enumerate(lay):
        for f in range(faces):
            res[f][l] = untile_level(blocks, gl[f], wb, hb, bpb) if h['tiled'] else None
    return h, res, total * bpb


# ---------------------------------------------------------------- block codecs
def _565(c):
    c = c.astype(np.uint32)
    r = (c >> 11) & 31; g = (c >> 5) & 63; b = c & 31
    return np.stack([(r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2)], -1).astype(np.int32)


def decode_bc1_color(blk, four_always=False):
    """blk (N,8) uint8 -> (N,16,4) uint8 RGBA."""
    c0 = blk[:, 0].astype(np.uint16) | (blk[:, 1].astype(np.uint16) << 8)
    c1 = blk[:, 2].astype(np.uint16) | (blk[:, 3].astype(np.uint16) << 8)
    p0, p1 = _565(c0), _565(c1)
    four = (c0 > c1) | four_always
    pal = np.zeros((len(blk), 4, 4), np.int32)
    pal[:, 0, :3] = p0; pal[:, 1, :3] = p1; pal[:, :, 3] = 255
    pal[:, 2, :3] = np.where(four[:, None], (2 * p0 + p1) // 3, (p0 + p1) // 2)
    pal[:, 3, :3] = np.where(four[:, None], (p0 + 2 * p1) // 3, 0)
    pal[:, 3, 3] = np.where(four, 255, 0)
    bits = blk[:, 4:8].astype(np.uint32)
    bits = bits[:, 0] | (bits[:, 1] << 8) | (bits[:, 2] << 16) | (bits[:, 3] << 24)
    ix = (bits[:, None] >> (2 * np.arange(16, dtype=np.uint32))) & 3
    return np.take_along_axis(pal, ix[:, :, None].astype(np.int64).repeat(4, 2), 1).astype(np.uint8)


def decode_bc4(blk):
    """blk (N,8) -> (N,16) uint8."""
    a0 = blk[:, 0].astype(np.int32); a1 = blk[:, 1].astype(np.int32)
    pal = np.zeros((len(blk), 8), np.int32)
    pal[:, 0] = a0; pal[:, 1] = a1
    big = a0 > a1
    for i in range(1, 7):
        pal[:, i + 1] = np.where(big, ((7 - i) * a0 + i * a1) // 7, 0)
    for i in range(1, 5):
        pal[:, i + 1] = np.where(big, pal[:, i + 1], ((5 - i) * a0 + i * a1) // 5)
    pal[:, 6] = np.where(big, pal[:, 6], 0); pal[:, 7] = np.where(big, pal[:, 7], 255)
    bits = np.zeros(len(blk), np.uint64)
    for i in range(6): bits |= blk[:, 2 + i].astype(np.uint64) << np.uint64(8 * i)
    ix = (bits[:, None] >> (np.uint64(3) * np.arange(16, dtype=np.uint64))) & np.uint64(7)
    return np.take_along_axis(pal, ix.astype(np.int64), 1).astype(np.uint8)


def decode_blocks(blk, kind):
    """kind: 'DXT1','DXT3','DXT5','DXN','ARGB' (BGRA bytes) -> (N,16,4) RGBA (for ARGB N pixels -> (N,1,4))."""
    if kind == 'DXT1': return decode_bc1_color(blk)
    if kind == 'DXT5':
        c = decode_bc1_color(blk[:, 8:], True); c[:, :, 3] = decode_bc4(blk[:, :8]); return c
    if kind == 'DXT3':
        c = decode_bc1_color(blk[:, 8:], True)
        a = blk[:, :8].astype(np.uint8)
        a = np.stack([a & 15, a >> 4], -1).reshape(len(blk), 16)
        c[:, :, 3] = a * 17; return c
    if kind == 'DXN':
        out = np.zeros((len(blk), 16, 4), np.uint8)
        out[:, :, 0] = decode_bc4(blk[:, :8]); out[:, :, 1] = decode_bc4(blk[:, 8:]); out[:, :, 3] = 255
        return out
    if kind == 'ARGB':
        return blk[:, [2, 1, 0, 3]].reshape(-1, 1, 4)
    raise ValueError(kind)


def blocks_to_image(blk, kind, w, h):
    px = decode_blocks(blk, kind)
    if kind == 'ARGB':
        return px.reshape(h, w, 4)
    wb, hb = max(1, (w + 3) // 4), max(1, (h + 3) // 4)
    img = px.reshape(hb, wb, 4, 4, 4).transpose(0, 2, 1, 3, 4).reshape(hb * 4, wb * 4, 4)
    return img[:h, :w]


def encode_red_color_block(r):
    """r (N,16) uint8 red values -> (N,8) DXT colour block with G=63, B=0, 4-colour mode, best R fit."""
    n = len(r)
    rf = r.astype(np.float32)
    lo5 = np.floor(rf.min(1) * 31 / 255).astype(np.int32); hi5 = np.ceil(rf.max(1) * 31 / 255).astype(np.int32)
    best_err = np.full(n, np.inf, np.float32); best = None
    for dl in (-1, 0, 1, 2):
        for dh in (1, 0, -1, -2):
            a5 = np.clip(hi5 + dh, 0, 31); b5 = np.clip(lo5 + dl, 0, 31)
            a5, b5 = np.maximum(a5, b5), np.minimum(a5, b5)
            ea = ((a5 << 3) | (a5 >> 2)).astype(np.float32); eb = ((b5 << 3) | (b5 >> 2)).astype(np.float32)
            ia, ib = ea.astype(np.int32), eb.astype(np.int32)
            pal = np.stack([ia, ib, (2 * ia + ib) // 3, (ia + 2 * ib) // 3], 1).astype(np.float32)
            d = np.abs(rf[:, :, None] - pal[:, None, :])
            ix = d.argmin(2); err = (d.min(2) ** 2).sum(1)
            better = err < best_err
            best_err = np.where(better, err, best_err)
            cand = (a5, b5, ix)
            if best is None: best = [c.copy() for c in cand]
            else:
                for j in range(3): best[j][better] = cand[j][better]
    a5, b5, ix = best
    c0 = (a5 << 11) | (63 << 5); c1 = (b5 << 11) | (63 << 5)
    # equal endpoints: c0 == c1 would select 3-colour mode in DXT1 decode, but DXT5 colour is always
    # 4-colour; keep indices 0 in that case
    ix = np.where((a5 == b5)[:, None], 0, ix)
    bits = (ix.astype(np.uint32) << (2 * np.arange(16, dtype=np.uint32))).sum(1).astype(np.uint32)
    out = np.zeros((n, 8), np.uint8)
    out[:, 0] = c0 & 255; out[:, 1] = c0 >> 8; out[:, 2] = c1 & 255; out[:, 3] = c1 >> 8
    for i in range(4): out[:, 4 + i] = (bits >> (8 * i)) & 255
    return out


def dxn_to_dxt5(blk):
    """(N,16) DXN blocks (after 8in16 swap) -> (N,16) DXT5 blocks: A = ch1 (verbatim), R = ch0."""
    out = np.empty_like(blk)
    out[:, :8] = blk[:, 8:]
    out[:, 8:] = encode_red_color_block(decode_bc4(blk[:, :8]))
    return out


# ---------------------------------------------------------------- conversion
def convert(xdata):
    """Xbox texture section data (bytes) -> PC texture section data (bytes). Raises on unsupported."""
    h, res, _ = xbox_levels(xdata)
    name = h['fmtname']
    if name not in PCFMT or not h['tiled']:
        raise NotImplementedError('format %s tiled=%s' % (name, h['tiled']))
    out = bytearray()
    for l in range(len(res[0])):  # PC order is level-major: for each level, all faces
        for face in res:
            lvl = face[l]
            if name == 'DXN':
                lvl = dxn_to_dxt5(lvl)
            out += lvl.tobytes()
    pcfmt = PCFMT[name]
    hdr = PHDR.pack(b'PCD9', pcfmt, len(out), 0, h['w'], h['h'], 32 if pcfmt == D3DFMT_A8R8G8B8 else 0,
                    h['mips'], h['flags'])
    return hdr + bytes(out)


def pc_kind(fmt):
    return {FOURCC['DXT1']: 'DXT1', FOURCC['DXT3']: 'DXT3', FOURCC['DXT5']: 'DXT5', D3DFMT_A8R8G8B8: 'ARGB'}[fmt]


def pc_levels(d):
    """PC section -> (hdr, [face][level] -> (blocks array, w, h))."""
    h = parse_pc(d)
    kind = pc_kind(h['fmt'])
    bpb = {'DXT1': 8, 'DXT3': 16, 'DXT5': 16, 'ARGB': 4}[kind]
    faces = 6 if h['flags'] & 0x8000 else 1
    a = np.frombuffer(d, np.uint8, offset=24)
    p = 0; res = [[] for f in range(faces)]
    for l in range(h['mips'] + 1):  # level-major (cubemaps: 6 faces per level)
        w, hh = max(1, h['w'] >> l), max(1, h['h'] >> l)
        n = w * hh if kind == 'ARGB' else max(1, (w + 3) // 4) * max(1, (hh + 3) // 4)
        for f in range(faces):
            res[f].append((a[p:p + n * bpb].reshape(n, bpb), w, hh)); p += n * bpb
    return h, kind, res


def pc_image(d, face=0, level=0):
    h, kind, res = pc_levels(d)
    blk, w, hh = res[face][level]
    return blocks_to_image(blk, kind, w, hh)


if __name__ == '__main__':
    # usage: tex_convert.py in_xbox_section.bin out_pc_section.bin
    src = open(sys.argv[1], 'rb').read()
    open(sys.argv[2], 'wb').write(convert(src))
