"""TR8 ShaderLib section (type 9) parser, Xbox360 (BE, Xenos microcode) and PC (LE, D3D9 SM3 bytecode).
Layout:  u8 kind (0 = vertex-shader lib, 256 permutation slots; 1 = pixel-shader lib, n slots), 3 pad bytes
         u32 tableBytes, u32 dataSize, u32 slot[tableBytes/4]  (offset relative to section+4, 0xFFFFFFFF = empty)
 entry @4+off: u32 junk (0xbaadf00d on Xbox), u32 entrySize (bytes from +8 = hash+blob), u64 hash, blob
 Xbox blob magic 0x102A1100 (pixel) / 0x102A1101 (vertex); PC blob = D3D9 token stream (ps_3_0 0xFFFF0300 / vs_3_0 0xFFFE0300).
Several slots may point at the same entry (dedup)."""
import struct
def parse(d, endian):
    e = '>' if endian in ('be', '>') else '<'
    kind = d[0]
    tb, ds = struct.unpack_from(e + 'II', d, 4)
    slots = list(struct.unpack_from(e + '%dI' % (tb // 4), d, 12))
    entries = {}
    for o in set(s for s in slots if s != 0xffffffff):
        junk, size = struct.unpack_from(e + 'II', d, 4 + o)
        h = d[4 + o + 8:4 + o + 16]
        blob = d[4 + o + 16:4 + o + 8 + size]
        entries[o] = dict(hash=h, blob=blob, size=size, junk=junk)
    return dict(kind=kind, tableBytes=tb, dataSize=ds, slots=slots, entries=entries)
def slot_hashes(lib):
    return [lib['entries'][s]['hash'] if s != 0xffffffff else None for s in lib['slots']]
def build(kind, slot_blobs, endian='le', junk=None):
    """slot_blobs: list (per slot) of (hash8, blob) or None. Identical (hash,blob) share an entry. Returns section bytes."""
    e = '>' if endian in ('be', '>') else '<'
    n = len(slot_blobs); tb = 4 * n
    data = bytearray(); offs = {}; slots = []
    base = 8 + tb  # offsets are relative to section+4; data starts after table at section+12+tb
    for sb in slot_blobs:
        if sb is None: slots.append(0xffffffff); continue
        key = (bytes(sb[0]), bytes(sb[1]))
        if key not in offs:
            offs[key] = base + len(data)
            j = junk if junk is not None else 0
            data += struct.pack(e + 'II', j, 8 + len(sb[1])) + key[0] + key[1]
        slots.append(offs[key])
    hdr = bytes([kind, 0, 0, 0]) + struct.pack(e + 'II', tb, len(data)) + struct.pack(e + '%dI' % n, *slots)
    return hdr + bytes(data)

def _ctab(d, o, e):
    """Parse D3DXSHADER_CONSTANTTABLE at d[o:]; returns (target, [(name, regset, regidx, regcount)])."""
    size, creator, version, n, cinfo, flags, target = struct.unpack_from(e + '7I', d, o)
    out = []
    for k in range(n):
        name_off, rs, ri, rc, _res, ti, dv = struct.unpack_from(e + 'IHHHHII', d, o + cinfo + 20 * k)
        end = d.find(b'\0', o + name_off)
        out.append((d[o + name_off:end].decode('latin1'), rs, ri, rc))
    return version, out
def constants(blob, platform):
    """Constant table of one shader blob. platform 'x' (Xenos container) or 'p' (D3D9 bytecode)."""
    try:
        if platform == 'x':
            ct_off = struct.unpack_from('>I', blob, 0x10)[0]
            return _ctab(blob, ct_off + 4, '>')
        # D3D9: version token then comment tokens; find CTAB
        i = blob.find(b'CTAB')
        if i < 0: return None, []
        return _ctab(blob, i + 4, '<')
    except Exception:
        return None, []
import re as _re
_HASHY = _re.compile(r'_[0-9A-F]{12,18}(?=_|$)')
def norm_name(n):
    """p_default_Material_0A00E06C184185_Texture -> p_default_Material_#_Texture (hash parts stripped)."""
    return _HASHY.sub('_#', n)
