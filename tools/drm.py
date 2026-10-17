import struct, zlib
def cdrm_decode(d, endian='be'):
    """Return raw DRM bytes from a CDRM container; pass through if not CDRM."""
    if d[:4] not in (b'CDRM', b'MRDC'): return d
    e = '>' if endian == 'be' else '<'
    n, = struct.unpack(e + 'I', d[8:12])
    ents = [struct.unpack(e + 'II', d[16 + 8*i:24 + 8*i]) for i in range(n)]
    pos = (16 + 8*n + 15) & ~15
    out = bytearray()
    for u, c in ents:
        blk = d[pos:pos + c]
        out += zlib.decompress(blk) if (u & 0xff) == 2 else blk
        pos = (pos + c + 15) & ~15
    return bytes(out)

SECTION_TYPES = {0:'Data',2:'Animation',5:'Texture',6:'Wave',7:'DTPData',9:'Shader',1:'Empty',3:'Pushbuffer',4:'Dtp',8:'Material',10:'Material',11:'Object'}
def parse_drm(d, endian):
    e = '>' if endian == 'be' else '<'
    ver, namesz, padsz, u0, u1, n = struct.unpack(e + 'iiiiii', d[:24])
    secs = []
    p = 24
    for i in range(n):
        size, typ, pad, vid, packed, sid, spec = struct.unpack(e + 'iBBHIII', d[p:p+20]); p += 20
        secs.append(dict(i=i, size=size, type=typ, ver=vid, packed=packed, nreloc=packed >> 8, flags=packed & 0xff, id=sid, spec=spec))
    p += namesz + padsz
    # relocations first then data per section, in order
    for s in secs:
        s['reloc_off'] = p; s['reloc_bytes'] = s['nreloc']; p += s['reloc_bytes']
        s['data_off'] = p; p += s['size']
    return dict(ver=ver, namesz=namesz, padsz=padsz, u0=u0, u1=u1), secs, p

def sections_with_data(raw, endian):
    h, secs, end = parse_drm(raw, endian)
    for s in secs:
        s['reloc'] = raw[s['reloc_off']:s['reloc_off'] + s['reloc_bytes']]
        s['data'] = raw[s['data_off']:s['data_off'] + s['size']]
    return h, secs
