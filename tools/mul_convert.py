"""Xbox cinstream .mul (cdc multiplexed cinematic stream) -> PC .mul.

Format (verified on base pairs 001_pro_corridor / 010_pro_surprise / 080_tha_yacht, Xbox layer vs PC bigfile):
  header 0x800 B, u32 words (platform endian): [0] sample rate, [1] -1, [2] total samples, [3] channels (2), [8],[9] 1,
          [14] float duration-ish, [15] 1.0, rest 0.
  blocks {u32 type (0 audio, 1 cine), u32 size, u32 a, u32 b} + payload, contiguous, no padding.
  PC order: C0 (CINE header), A0, then (A_i, C_i) for i = 1..N-1, then C_N  (N = #cine blocks - 1 audio blocks).
  PC audio block i covers samples [a_i, a_{i+1}), a_i = floor(i * rate/30 / 256) * 256 (1280/1536-sample blocks);
          payload = {u32 nbytes, 0, 0, 0} + stereo FMOD IMA ADPCM: per 64 samples a 36-B left block then a 36-B right block
          (s16 pred, u8 index, u8 0, 32 B nibbles), the same mono block format as wave_convert.
  Xbox audio = XMA (4128-B blocks, fewer than frames, a = sample position): NOT decoded here (stereo XMA1 multiplex)
          -> PC audio is DIGITAL SILENCE of the right length (cinematic plays without VO/music).
  CINE payload: big-endian u32 words -> byte-swap every word (99.9% of words on the base pairs) EXCEPT
          block 0 scene name (char[64] @0xc) and subtitle tails {u32 len, UTF-8 text} that end a frame block (copied raw).
usage: mul_convert.py XBOX.mul OUT.mul   |   mul_convert.py validate NAME   (NAME in work/mul/{NAME}.xb.mul/.pc.mul)"""
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def blocks(d, E):
    o = 0x800; out = []
    while o + 16 <= len(d):
        t, sz, a, b = struct.unpack_from(E + '4I', d, o)
        if o + 16 + sz > len(d): raise ValueError('bad block at %x' % o)
        out.append((t, a, b, d[o + 16:o + 16 + sz])); o += 16 + sz
    if o != len(d): raise ValueError('trailing bytes')
    return out

def _texty(b):
    """subtitle text: UTF-8 (lines '<n>\r<text>\r'), allow a few odd bytes"""
    b = b.rstrip(b'\0')
    if len(b) < 2: return False
    s = b.decode('utf-8', errors='replace')
    good = sum(ch.isprintable() or ch in '\r\n\t' for ch in s if ch != '\ufffd')
    return good >= 0.9 * len(s) and '\r' in s

def subtitle_at(p):
    """offset of the {u32 len, text} subtitle tail of a BE frame block, or None"""
    for w in range(8, len(p) - 4, 4):
        L = struct.unpack_from('>I', p, w)[0]
        e = w + 4 + L
        if 2 <= L and len(p) - 16 < e <= len(p) and not p[e:].strip(b'\0') and _texty(p[w + 4:e]):   # text + zero pad to 16
            return w
    return None

def conv_cine(p, first, ids=None):
    n4 = len(p) // 4 * 4
    out = bytearray(len(p))
    for w in range(0, n4, 4): out[w:w + 4] = p[w:w + 4][::-1]
    out[n4:] = p[n4:]
    if first:
        out[0xc:0x4c] = p[0xc:0x4c]                      # scene name
        if ids is not None:
            # actor intro unique ids (type-113 space, PC numbering differs for base levels): a field is an id when it is
            # followed by 0xffffffff ({.., ID, -1, n}) or sits after an offset pair {X, f, X, ID} (word[-1] == word[-3]).
            # Validated on 21 base pairs (tools/mul_convert.py validate): reproduces the PC words wherever the id is mapped.
            W = struct.unpack_from('>%dI' % (n4 // 4), p, 0)
            # first record {U, 1, U, level intro id} = the cinematic's UNIT: U is a StreamUnitID (objlist index, type-110 space:
            # Xbox and PC number units differently, e.g. L2_norsehall 69->53, L3_caverns_start 78->62, dlc_level1_start 88->89).
            # Every reference to it in the header holds the same value (validated: 092_tha_arch / 120_man_vault exact).
            if W[0x4c // 4] == W[0x54 // 4] and W[0x50 // 4] == 1:
                u = W[0x4c // 4]; nu = ids(110, u)
                if nu != u:
                    for k in range(0x4c // 4, len(W)):
                        if W[k] == u: struct.pack_into('<I', out, 4 * k, nu)
            xs = {W[k] for k in range(len(W) - 2) if W[k] and W[k] == W[k + 2] and W[k + 1] in (0, 1)}   # record keys {X, f, X}
            for o in range(0x4c, n4 - 4, 4):
                v = struct.unpack_from('>I', p, o)[0]
                if not (4096 <= v < 0x100000) or v in xs: continue      # intro ids >= 4096 (base 5195..9346, DLC 6713..12240); smaller = record refs
                nxt = struct.unpack_from('>I', p, o + 4)[0]
                X = p[o - 4:o] if o >= 12 else b''
                pair = X and X == p[o - 12:o - 8] and X != b'\0\0\0\0' and X != p[o:o + 4] and nxt in (0, 0xffffffff)
                if nxt == 0xffffffff or pair:
                    struct.pack_into('<I', out, o, ids(113, v))
    else:
        s = subtitle_at(p)
        if s is not None: out[s + 4:] = p[s + 4:]
    return bytes(out)

def ima_silence(nsamples):
    blk = struct.pack('<hBB', 0, 0, 0) + b'\0' * 32         # one 36-B mono block = 64 samples of silence
    return (blk + blk) * (nsamples // 64)

def convert(xd, ids=None):
    hx = list(struct.unpack_from('>512I', xd, 0))
    B = blocks(xd, '>')
    C = [b for b in B if b[0] == 1]
    if not C: raise ValueError('no cine blocks')
    rate = hx[0]; N = len(C) - 1
    a = [(i * rate // 30 // 256) * 256 for i in range(N + 1)]
    hdr = list(hx); hdr[2] = a[N]
    out = bytearray(struct.pack('<512I', *hdr))
    out[0x38:0x40] = xd[0x38:0x40][:4][::-1] + xd[0x3c:0x40][::-1]   # floats are plain u32 swaps too (kept explicit)
    def put(t, payload, a_=0):
        out.extend(struct.pack('<4I', t, len(payload), a_, 0)); out.extend(payload)
    def audio(i):
        data = ima_silence(a[i + 1] - a[i])
        put(0, struct.pack('<4I', len(data), 0, 0, 0) + data, a[i])
    put(1, conv_cine(C[0][3], True, ids))
    audio(0)
    for i in range(1, N):
        audio(i); put(1, conv_cine(C[i][3], False))
    put(1, conv_cine(C[N][3], False))
    return bytes(out)

def validate(name):
    W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work', 'mul')
    xd = open(os.path.join(W, name + '.xb.mul'), 'rb').read(); pd = open(os.path.join(W, name + '.pc.mul'), 'rb').read()
    import dlc_generic as DG
    od = convert(xd, DG.DlcIds(None, None))
    O = blocks(od, '<'); P = blocks(pd, '<')
    print(name, 'blocks ours/pc', len(O), len(P), 'order equal', [b[0] for b in O] == [b[0] for b in P],
          'audio a equal', sum(1 for o, p in zip(O, P) if o[0] == 0 and o[1] == p[1]), '/', sum(1 for p in P if p[0] == 0),
          'audio size equal', sum(1 for o, p in zip(O, P) if o[0] == 0 and len(o[3]) == len(p[3])))
    oc = [b[3] for b in O if b[0] == 1]; pc = [b[3] for b in P if b[0] == 1]
    tot = bad = same = diffsz = 0
    for i, (o, p) in enumerate(zip(oc, pc)):
        if len(o) != len(p): diffsz += 1; continue
        s = subtitle_at(blocks(xd, '>')[0][3]) if False else None
        n = len(o) // 4
        ww = [w for w in range(0, n * 4, 4) if o[w:w + 4] != p[w:w + 4]]
        # subtitle text differs per platform build: ignore words inside a detected subtitle tail
        xs = [b[3] for b in blocks(xd, '>') if b[0] == 1][i]
        st = subtitle_at(xs) if i else None
        if st is not None: ww = [w for w in ww if w < st + 4]
        tot += n; bad += len(ww); same += not ww
    print('   cine blocks exact', same, '/', len(pc), 'size-different', diffsz, 'wrong words', bad, 'of', tot)

if __name__ == '__main__':
    if sys.argv[1] == 'validate':
        for n in sys.argv[2:]: validate(n)
    else:
        ids = None
        try:
            import dlc_generic as DG; ids = DG.DlcIds(None, None)
        except Exception: pass
        open(sys.argv[2], 'wb').write(convert(open(sys.argv[1], 'rb').read(), ids)); print('wrote', sys.argv[2])
