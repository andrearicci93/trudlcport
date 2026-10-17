"""Xbox 360 (big-endian) -> PC (little-endian) conversion of generic DRM sections.

convert(xdata, sec_type, xreloc_blob, ids=IdMapper, sec_id=None) -> (pc_data, pc_reloc_blob)

Common rules (all types):
  * relocation blob: parse BE, write LE (structure is platform independent, verified 100%)
  * pointer fields (internal/external reloc offsets): 32-bit swap (raw values are kept)
  * id-reference fields (idref / idref_a): 32-bit swap + Xbox->PC id remap for the given section type
Per-type field layouts: see the conv_* functions and NOTES.md "Generic converter".
"""
import struct, sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_reloc as R
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work', 'generic')

class IdMapper:
    """Xbox id -> PC id per section type. Unknown ids (DLC-new) are allocated above the PC maximum
    (alloc_base[type]) unless strict, in which case KeyError is raised."""
    def __init__(self, path=os.path.join(W, 'idmap.json'), alloc_base=None, strict=False):
        d = json.load(open(path)) if path and os.path.exists(path) else {}
        self.m = {int(t): {int(a): b for a, b in v.items()} for t, v in d.items()}
        self.alloc = dict(alloc_base or {})
        self.new = {}
        self.strict = strict
        self.missing = 0
    def __call__(self, t, xid):
        m = self.m.get(t, {})
        if xid in m: return m[xid]
        if (t, xid) in self.new: return self.new[t, xid]
        self.missing += 1
        if self.strict: raise KeyError((t, xid))
        if t not in self.alloc: return xid
        self.alloc[t] += 1
        self.new[t, xid] = self.alloc[t]
        return self.alloc[t]

def sw32(b, out, o):
    out[o:o + 4] = b[o:o + 4][::-1]
def sw16(b, out, o):
    out[o:o + 2] = b[o:o + 2][::-1]

def base_swap32(x):
    """swap every aligned 32-bit word, keep trailing bytes."""
    out = bytearray(x)
    n = len(x) // 4 * 4
    out[:n] = b''.join(x[i:i + 4][::-1] for i in range(0, n, 4)) if n else b''
    return out

def apply_relocs(x, out, rel, ids):
    for o in rel.pointer_offsets():
        sw32(x, out, o)
    for o, t in rel.id_offsets().items():
        v, = struct.unpack_from('>I', x, o)
        struct.pack_into('<I', out, o, ids(t, v) if v not in (0, 0xffffffff) else v)

# ------------------------------------------------------------------------------------- per type
def conv_default(x, rel, ids, sid):
    out = base_swap32(x)
    apply_relocs(x, out, rel, ids)
    return out

def conv_obj(x, rel, ids, sid):
    """Type 11, 140 bytes: u32 dtp ids[3] (idref), ..., u32 objectId @20 (= section id), rest u32."""
    out = base_swap32(x)
    apply_relocs(x, out, rel, ids)
    if len(x) >= 24:
        v, = struct.unpack_from('>I', x, 20)
        struct.pack_into('<I', out, 20, ids(11, v))
    return out

ANIM_STATS = {'ok': 0, 'fail': 0}
def conv_anim(x, rel, ids, sid):
    """Type 2 animation (G2AnimKeylist-like), layout verified on base pairs:
      0x00-0x2f  12 x u32/float
      0x30 u16 animId (= section id, remapped)  0x32 u16 keyCount  0x34 u16 timePerKey
      0x36 u8 segCount  0x37 u8   0x38 u8 nExtra, u8, u16  0x3c u32 (size-0x3c)  0x40 u32
      0x44 u32 L ; [0x48, 0x44+L) raw bytes (channel bit masks)
      then a stream of channel segments until the end:
        {u16 kind, u16 n} kind 0: keyCount floats; kind 1: 1 float; kind 2: (n-1) u8 time deltas
        padded to 4, then n floats.  A header whose first u16 is negative (s16 extra-channel id)
        introduces an extra channel {s16 id, u16 x} followed by one segment."""
    out = base_swap32(x)
    n = len(x)
    if n < 0x48:
        return out
    out[0x30:0x38] = x[0x30:0x38]
    v, = struct.unpack_from('>H', x, 0x30)
    struct.pack_into('<H', out, 0x30, ids(2, v) & 0xffff)
    sw16(x, out, 0x32); sw16(x, out, 0x34)
    out[0x38:0x3a] = x[0x38:0x3a]; sw16(x, out, 0x3a)      # u8 extraChannelCount, u8, u16
    kc, = struct.unpack_from('>H', x, 0x32)
    ml, = struct.unpack_from('>I', x, 0x44)
    pos = min(0x44 + ml, n)
    out[0x48:pos] = x[0x48:pos]
    ok = True
    while pos + 4 <= n:
        t, c = struct.unpack_from('>HH', x, pos)
        sw16(x, out, pos); sw16(x, out, pos + 2)
        pos += 4
        if t == 0: pos += 4 * kc
        elif t == 1: pos += 4
        elif t == 2:
            nb = max(c - 1, 0)
            out[pos:pos + (nb + 3) // 4 * 4] = x[pos:pos + (nb + 3) // 4 * 4]
            pos += (nb + 3) // 4 * 4 + 4 * c
        elif t >= 0x8000: pass                       # extra channel header, segment follows
        else: ok = False; break
    ok = ok and pos == n
    ANIM_STATS['ok' if ok else 'fail'] += 1
    apply_relocs(x, out, rel, ids)
    return out

CONV = {11: conv_obj, 2: conv_anim}

def convert(xdata, sec_type, xreloc, ids, sec_id=None):
    rel = R.parse(xreloc, 'be')
    f = CONV.get(sec_type, conv_default)
    return bytes(f(xdata, rel, ids, sec_id)), R.write(rel, 'le')

# ------------------------------------------------------------------------------------- evaluation
def evaluate(types=(0, 2, 7, 8, 11, 13), verbose=0):
    import pickle, collections
    from generic_ids import section_matches
    from generic_cache import load_pairs
    P = load_pairs()
    ids = IdMapper()
    st = collections.Counter(); bad = collections.defaultdict(list)
    for nm, (x, p) in P.items():
        sx, sp = x[1], p[1]
        for i, j, strength in section_matches(sx, sp, ids.m):
            a, b = sx[i], sp[j]
            t = a['type']
            if t not in types or a['size'] != b['size']: continue
            d, r = convert(a['data'], t, a['reloc'], ids, a['id'])
            st[t, 'n'] += 1
            st[t, 'reloc_ok'] += r == b['reloc']
            ok = d == b['data']
            st[t, 'exact'] += ok
            if not ok:
                nb = sum(1 for k in range(len(d)) if d[k] != b['data'][k])
                st[t, 'bad_bytes'] += nb
                if len(bad[t]) < 2000: bad[t].append((nm, i, j, nb))
            st[t, 'bytes'] += len(d)
    for t in sorted({k[0] for k in st}):
        n = st[t, 'n']
        print('type %2d: %6d pairs  exact %6d (%.2f%%)  reloc_exact %.2f%%  wrong bytes %.4f%%' % (
            t, n, st[t, 'exact'], 100 * st[t, 'exact'] / n, 100 * st[t, 'reloc_ok'] / n, 100 * st[t, 'bad_bytes'] / max(1, st[t, 'bytes'])))
    return st, bad

if __name__ == '__main__':
    ts = tuple(int(a) for a in sys.argv[1:]) or (0, 2, 7, 8, 11, 13)
    st, bad = evaluate(ts)
    import pickle
    pickle.dump(bad, open(os.path.join(W, 'eval_bad.pkl'), 'wb'))
