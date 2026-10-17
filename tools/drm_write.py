"""TR8 DRM (version 19) reader/writer + CDRM container encoder.

Raw DRM layout (platform endian; see NOTES.md):
  header 24B : i32 ver(19), i32 nameSz, i32 padSz, i32 u0(0), i32 u1(0), i32 numSections
  numSections x SectionInfo 20B : i32 size, u8 type, u8 pad(0), u16 ver, u32 packed (low 8 = flags,
                                  >>8 = reloc blob BYTES), u32 id, u32 specMask
  nameSz bytes : NUL-terminated names of DRMs this one depends on (e.g. "g_pda\\0wp_uzi\\0"), then padSz bytes
  per section, in order: reloc blob (packed>>8 bytes) then data (size bytes).  No padding anywhere.
CDRM (both platforms, here written little-endian for PC):
  16B header 'CDRM', u32 0, u32 numBlocks, u32 0 ; numBlocks x {u32 usize<<8 | 2(zlib) / 1(raw), u32 csize}
  data starts at align16(16 + 8*numBlocks); each block's compressed bytes, next block at align16(end);
  NO padding after the last block.  Blocks are 256 KiB of the raw DRM (last one shorter), zlib level 9
  (byte-identical to the shipped PC files).

API:
  read(raw_or_cdrm, endian) -> Drm(hdr, names(bytes), sections=[Section])
  Drm.write(endian) -> raw bytes ;  cdrm_encode(raw, endian='le') -> CDRM bytes
Usage: python3 -I tools/drm_write.py [N]   round-trip test on the first N PC bigfile DRMs (default all)
"""
import struct, zlib, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BLOCK = 0x40000

class Section:
    __slots__ = ('type', 'id', 'flags', 'ver', 'spec', 'reloc', 'data', 'pad')
    def __init__(self, type, id, data, reloc=b'', flags=0, ver=0, spec=0xffffffff, pad=0):
        self.type, self.id, self.data, self.reloc = type, id, bytes(data), bytes(reloc)
        self.flags, self.ver, self.spec, self.pad = flags, ver, spec, pad
    def __repr__(self):
        return 'Section(type=%d id=%d size=%d reloc=%d flags=%d)' % (self.type, self.id, len(self.data), len(self.reloc), self.flags)

class Drm:
    def __init__(self, sections, names=b'', pad=b'', ver=19, u0=0, u1=0):
        self.sections, self.names, self.pad, self.ver, self.u0, self.u1 = sections, names, pad, ver, u0, u1
    def write(self, endian='le'):
        e = '>' if endian == 'be' else '<'
        out = bytearray(struct.pack(e + '6i', self.ver, len(self.names), len(self.pad), self.u0, self.u1, len(self.sections)))
        for s in self.sections:
            assert len(s.reloc) < 1 << 24 and s.flags < 256
            out += struct.pack(e + 'iBBHIII', len(s.data), s.type, s.pad, s.ver, len(s.reloc) << 8 | s.flags, s.id, s.spec)
        out += self.names + self.pad
        for s in self.sections:
            out += s.reloc + s.data
        return bytes(out)

def cdrm_decode(d, endian):
    from drm import cdrm_decode as dec
    return dec(d, endian)

def read(d, endian):
    d = cdrm_decode(d, endian)
    e = '>' if endian == 'be' else '<'
    ver, namesz, padsz, u0, u1, n = struct.unpack_from(e + '6i', d, 0)
    infos = [struct.unpack_from(e + 'iBBHIII', d, 24 + 20 * i) for i in range(n)]
    p = 24 + 20 * n
    names = d[p:p + namesz]; pad = d[p + namesz:p + namesz + padsz]; p += namesz + padsz
    secs = []
    for size, typ, spad, sver, packed, sid, spec in infos:
        nr = packed >> 8
        secs.append(Section(typ, sid, d[p + nr:p + nr + size], d[p:p + nr], packed & 0xff, sver, spec, spad))
        p += nr + size
    if p != len(d): raise ValueError('DRM size mismatch %d != %d' % (p, len(d)))
    return Drm(secs, names, pad, ver, u0, u1)

def cdrm_encode(raw, endian='le', block=BLOCK, level=9):
    e = '>' if endian == 'be' else '<'
    blocks = [raw[i:i + block] for i in range(0, len(raw), block)] or [b'']
    comp = [zlib.compress(b, level) for b in blocks]
    out = bytearray(struct.pack(e + '4sIII', b'CDRM', 0, len(blocks), 0))
    if endian == 'be': out[:4] = b'CDRM'          # magic is the same byte string on both platforms
    for b, c in zip(blocks, comp):
        out += struct.pack(e + 'II', len(b) << 8 | 2, len(c))
    for k, c in enumerate(comp):
        out += b'\0' * (-len(out) % 16)
        out += c
    return bytes(out)

if __name__ == '__main__':
    from archive import Archive
    from names import load, L, crc
    lim = int(sys.argv[1]) if len(sys.argv) > 1 else None
    pc = Archive('/path/to/trudlcport/pc/bigfile.000', 'le')
    pcn = load(L + 'Tomb Raider Underworld (PC).txt')
    names = sorted(n for n in pcn.values() if n.lower().startswith('pc-w\\') and n.lower().endswith('.drm'))[:lim]
    st = {'drm': 0, 'raw_ok': 0, 'cdrm_files': 0, 'cdrm_ok': 0, 'sections': 0}
    for nm in names:
        for r in pc.find(crc(nm)):
            f = pc.read(r)
            raw = cdrm_decode(f, 'le')
            D = read(raw, 'le')
            st['drm'] += 1; st['sections'] += len(D.sections)
            w = D.write('le')
            st['raw_ok'] += w == raw
            if f[:4] == b'CDRM':
                st['cdrm_files'] += 1
                st['cdrm_ok'] += cdrm_encode(w, 'le') == f
                if cdrm_encode(w, 'le') != f and st['cdrm_files'] - st['cdrm_ok'] < 4: print('cdrm mismatch', nm, len(f))
    print(st)
