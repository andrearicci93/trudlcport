"""Shared helpers for rendering-data work (mesh/material/shader). TR8 (Underworld) Xbox360 <-> PC.
Relocation block layout (verified on Xbox+PC base pairs, sizes add up for every section):
  u32 nInternal, nExternal, nTable3, nTable4, nResRef
  Internal[nInternal]  : {u32 offset, u32 target}          pointer inside this section (offset -> target)
  External[nExternal]  : {u32 offset, u32 packed}          pointer into another section of the DRM
  Table3[nTable3]      : u32                               (object/ID refs, 4 bytes each)
  Table4[nTable4]      : ?? (never non-zero in survey)
  ResRef[nResRef]      : u32 (sectionType << 25) | (offset >> 2)   field at offset holds a section id of that type
                         (type 5 texture, 9 shader, 10 material ...) resolved by id at load time.
"""
import sys, json, struct, pickle, os
sys.path.insert(0, '/path/to/trudlcport/tools')
ROOT = '/path/to/trudlcport/'
WORK = ROOT + 'work/render/'

def parse_reloc(r, endian):
    e = '>' if endian == 'be' else '<'
    if not r: return dict(internal=[], external=[], t3=[], t4=b'', res=[])
    a, b, c, d, n = struct.unpack(e + '5I', r[:20]); p = 20
    internal = [struct.unpack_from(e + 'II', r, p + 8 * i) for i in range(a)]; p += 8 * a
    external = [struct.unpack_from(e + 'II', r, p + 8 * i) for i in range(b)]; p += 8 * b
    t3 = list(struct.unpack_from(e + '%dI' % c, r, p)); p += 4 * c
    t4len = len(r) - p - 4 * n
    t4 = r[p:p + t4len]; p += t4len
    res = [((v >> 25), (v & 0x1ffffff) << 2) for v in struct.unpack_from(e + '%dI' % n, r, p)]
    return dict(internal=internal, external=external, t3=t3, t4=t4, t4n=d, res=res)

def build_reloc(R, endian):
    e = '>' if endian == 'be' else '<'
    out = bytearray(struct.pack(e + '5I', len(R['internal']), len(R['external']), len(R['t3']), R.get('t4n', 0), len(R['res'])))
    for o, t in R['internal']: out += struct.pack(e + 'II', o, t)
    for o, t in R['external']: out += struct.pack(e + 'II', o, t)
    for v in R['t3']: out += struct.pack(e + 'I', v)
    out += R['t4']  # never seen non-empty; byte order unknown
    for typ, off in R['res']: out += struct.pack(e + 'I', (typ << 25) | (off >> 2))
    return bytes(out)

def pair_names():
    return json.load(open(WORK + 'pairnames.json'))

_cache_dir = WORK + 'cache/'
def load_pair(name):
    """(xbox (hdr,secs), pc (hdr,secs)) with on-disk pickle cache."""
    os.makedirs(_cache_dir, exist_ok=True)
    fn = _cache_dir + name.replace('\\', '__') + '.pkl'
    if os.path.exists(fn):
        return pickle.load(open(fn, 'rb'))
    from pairs import xbox_drm, pc_drm
    v = (xbox_drm(name), pc_drm(name))
    pickle.dump(v, open(fn, 'wb'))
    return v
