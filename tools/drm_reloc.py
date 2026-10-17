"""TR8 (cdcEngine DRM v19) per-section relocation table: parser / writer / helpers.

Layout (verified on all 1054 Xbox<->PC base DRM pairs, both endians; see NOTES.md "Generic converter"):
  The blob that precedes each section's data has length SectionInfo.packed >> 8 (bytes, not a count).
  Empty blob (0 bytes) = no relocations.  Otherwise:
    u32 counts[5]                      header, 20 bytes, platform endian
    counts[0] x {u32 offset, u32 target}   INTERNAL pointers: *(u32*)(data+offset) = base(this) + target
    counts[1] x u64 packed              EXTERNAL pointers into another section of the SAME DRM:
                                         bits  0..13  section index (in this DRM's section list)
                                         bits 14..37  source offset / 4 (in this section)
                                         bits 38..63  target offset (byte offset in target section)
    counts[2] x u32 packed              ID references, kind A (only seen with type 5 = texture ids):
                                         bits 25..31 section type, bits 0..24 offset/4; the u32 at
                                         data+offset holds a section id of that type
    counts[3] x u32                     never non-zero in the corpus (assumed 4-byte entries)
    counts[4] x u32 packed              ID references (resource refs): same packing as kind A. Seen types:
                                         5 texture, 7 DTPData, 8 Script, 9 ShaderLib, 10 Material, 12 Mesh.
                                         The u32 at data+offset is the referenced section id
                                         (100% of 2.6M entries resolve to an existing id of that type).
  Byte-swapping: header/internal/kindA/resource entries are u32 swaps, external entries are a u64 swap.
"""
import struct

class Reloc:
    __slots__ = ('internal', 'external', 'idref_a', 'unk3', 'idref')
    def __init__(self, internal=None, external=None, idref_a=None, unk3=None, idref=None):
        self.internal = internal or []      # [(offset, target)]
        self.external = external or []      # [(section_index, src_offset, dst_offset)]
        self.idref_a = idref_a or []        # [(sec_type, offset)]
        self.unk3 = unk3 or []              # [raw u32]
        self.idref = idref or []            # [(sec_type, offset)]
    def empty(self):
        return not (self.internal or self.external or self.idref_a or self.unk3 or self.idref)
    def __eq__(self, o):
        return all(getattr(self, k) == getattr(o, k) for k in self.__slots__)
    def __repr__(self):
        return 'Reloc(int=%d ext=%d idA=%d unk3=%d id=%d)' % tuple(len(getattr(self, k)) for k in self.__slots__)

    # ---- positions of fields that are 32-bit and must be treated specially -----------------
    def pointer_offsets(self):
        """Byte offsets (in section data) of all 32-bit pointer fields (internal + external)."""
        return sorted([o for o, _ in self.internal] + [s for _, s, _ in self.external])
    def id_offsets(self):
        """{offset: section_type} of all 32-bit section-id fields."""
        d = {o: t for t, o in self.idref_a}
        d.update({o: t for t, o in self.idref})
        return d

def pack_ext(si, src, dst):
    assert src % 4 == 0 and si < 1 << 14 and src >> 2 < 1 << 24 and dst < 1 << 26
    return si | (src >> 2) << 14 | dst << 38

def unpack_ext(v):
    return v & 0x3fff, ((v >> 14) & 0xffffff) << 2, v >> 38

def parse(blob, endian):
    """blob: relocation bytes of one section; endian 'be'/'le' or '>'/'<'."""
    e = '>' if endian in ('be', '>') else '<'
    if not blob: return Reloc()
    n = struct.unpack(e + '5I', blob[:20]); o = 20
    r = Reloc()
    for _ in range(n[0]):
        r.internal.append(struct.unpack(e + 'II', blob[o:o + 8])); o += 8
    for _ in range(n[1]):
        r.external.append(unpack_ext(struct.unpack(e + 'Q', blob[o:o + 8])[0])); o += 8
    for _ in range(n[2]):
        v, = struct.unpack(e + 'I', blob[o:o + 4]); o += 4
        r.idref_a.append((v >> 25, (v & 0x1ffffff) << 2))
    for _ in range(n[3]):
        r.unk3.append(struct.unpack(e + 'I', blob[o:o + 4])[0]); o += 4
    for _ in range(n[4]):
        v, = struct.unpack(e + 'I', blob[o:o + 4]); o += 4
        r.idref.append((v >> 25, (v & 0x1ffffff) << 2))
    if o != len(blob):
        raise ValueError('reloc blob length mismatch: parsed %d of %d bytes' % (o, len(blob)))
    return r

def write(r, endian):
    e = '>' if endian in ('be', '>') else '<'
    if r.empty(): return b''
    out = bytearray(struct.pack(e + '5I', len(r.internal), len(r.external), len(r.idref_a), len(r.unk3), len(r.idref)))
    for a, b in r.internal: out += struct.pack(e + 'II', a, b)
    for si, s, d in r.external: out += struct.pack(e + 'Q', pack_ext(si, s, d))
    for t, off in r.idref_a: out += struct.pack(e + 'I', t << 25 | off >> 2)
    for v in r.unk3: out += struct.pack(e + 'I', v)
    for t, off in r.idref: out += struct.pack(e + 'I', t << 25 | off >> 2)
    return bytes(out)

def check(r, data_size, sections=None):
    """Sanity check bounds; sections = list of dicts (with 'size') of the DRM. Returns list of problems."""
    bad = []
    for a, b in r.internal:
        if a + 4 > data_size or b > data_size: bad.append(('int', a, b))
    for si, s, d in r.external:
        if s + 4 > data_size or (sections is not None and (si >= len(sections) or d > sections[si]['size'])):
            bad.append(('ext', si, s, d))
    for t, off in r.idref_a + r.idref:
        if off + 4 > data_size: bad.append(('id', t, off))
    return bad

if __name__ == '__main__':
    # round trip test over the pair cache (both platforms) and optionally DLC archives
    import pickle, sys, os, collections
    P = pickle.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work', 'generic', 'pairs.pkl'), 'rb'))
    st = collections.Counter()
    for nm, (x, p) in P.items():
        for plat, (h, secs), e in (('xbox', x, 'be'), ('pc', p, 'le')):
            for s in secs:
                r = parse(s['reloc'], e)
                st[plat, 'sections'] += 1
                st[plat, 'roundtrip_ok' if write(r, e) == s['reloc'] else 'roundtrip_BAD'] += 1
                st[plat, 'bounds_ok' if not check(r, s['size'], secs) else 'bounds_BAD'] += 1
                st[plat, 'unk3_nonzero'] += bool(r.unk3)
    for k, v in sorted(st.items()): print(k, v)
