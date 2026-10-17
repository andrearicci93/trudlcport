"""Xbox 360 '!WAR' image .raw -> PC '!WAR' image .raw (Tomb Raider Underworld).

FORMAT (verified byte-exact against 257 base-game Xbox/PC pairs, see work/dlc_images/NOTES_agent.md):
  128-byte header = 32 u32 in PLATFORM endian (Xbox big, PC little; magic bytes 21 57 41 52 = '!WAR' on both):
   [0] magic  [1] 0x80 header size  [2] pixel data size  [3] format (3 = tiled on Xbox; 13 = linear, Xbox only)
   [4] flags (0x10/0x70, copied unchanged)  [5] width  [6] height  [7] pitch = width*4  [8] bpp 32  [9..12] 8,8,8,8
   [13..16] masks ff000000, ff, ff00, ff0000 (same value on both platforms)  [28],[29] = 0xffffffff, rest 0.
  Xbox pixels: 32-bit words big-endian A8R8G8B8, i.e. bytes A,R,G,B, stored in Xbox 360 2D tiled layout
    (32x32-pixel macro tiles, XGAddress2DTiledOffset, width/height padded to 32). format 13 instead = LINEAR rows with pitch padded
    to 64 pixels (256 bytes), height not padded (seen only on DLC image dlc_outfit_costume_n).
  PC pixels: linear, width*height*4 bytes, bytes B,G,R,A (little-endian A8R8G8B8), no padding; word[2] = w*h*4, word[3] = 3.
  Everything else in the header is identical on both platforms.
usage: tools/venv/bin/python -I tools/raw_image_convert.py selftest
       tools/venv/bin/python -I tools/raw_image_convert.py dlc          (writes work/dlc_images/{image,check,md5.txt})
       tools/venv/bin/python -I tools/raw_image_convert.py file IN.raw OUT.raw [OUT.png]
"""
import sys, os, struct
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
MAGIC = b'!WAR'

def tiled_index(w, h):
    """pixel index (in the tiled buffer) of every (y,x) of the padded w*h surface, 32bpp."""
    aw, ah = (w + 31) & ~31, (h + 31) & ~31
    y, x = np.mgrid[0:ah, 0:aw].astype(np.int64)
    macro = ((x >> 5) + (y >> 5) * (aw >> 5)) << 9
    micro = ((x & 7) + ((y & 0xE) << 2)) << 2
    off = macro + ((micro & ~0xF) << 1) + (micro & 0xF) + ((y & 1) << 4)
    byte = ((off & ~0x1FF) << 3) + ((y & 16) << 7) + ((off & 0x1C0) << 2) + (((((y & 8) >> 2) + (x >> 3)) & 3) << 6) + (off & 0x3F)
    return byte >> 2, ah, aw

def header(b, endian):
    if b[:4] != MAGIC: raise ValueError('bad magic %r' % b[:4])
    return list(struct.unpack(endian + '32I', b[:128]))

def decode_xbox(b):
    """-> (header words, HxWx4 uint8 array in B,G,R,A order)"""
    h = header(b, '>')
    fmt, w, ht, bpp = h[3], h[5], h[6], h[8]
    if bpp != 32 or h[1] != 128: raise ValueError('unsupported header %r' % h[:12])
    data = np.frombuffer(b, np.uint8, offset=128).reshape(-1, 4)
    if fmt == 3:
        idx, ah, aw = tiled_index(w, ht)
        if len(data) < ah * aw: raise ValueError('short data')
        px = data[idx].reshape(ah, aw, 4)[:ht, :w]
        if h[2] != ah * aw * 4: raise ValueError('data size word %d != %d' % (h[2], ah * aw * 4))
    elif fmt == 13:
        pitch = (w + 63) & ~63
        if len(data) < pitch * ht: raise ValueError('short data')
        px = data[:pitch * ht].reshape(ht, pitch, 4)[:, :w]
        if h[2] != pitch * ht * 4: raise ValueError('data size word %d != %d' % (h[2], pitch * ht * 4))
    else:
        raise ValueError('unknown format %d' % fmt)
    return h, np.ascontiguousarray(px[..., ::-1])   # A,R,G,B -> B,G,R,A

def decode_pc(b):
    h = header(b, '<')
    w, ht = h[5], h[6]
    if h[3] != 3 or h[8] != 32 or h[2] != w * ht * 4 or len(b) != 128 + w * ht * 4: raise ValueError('unexpected PC image %r len %d' % (h[:9], len(b)))
    return h, np.frombuffer(b, np.uint8, offset=128).reshape(ht, w, 4)

def xbox_to_pc(b):
    h, px = decode_xbox(b)
    ht, w = px.shape[:2]
    h = list(h); h[2] = w * ht * 4; h[3] = 3
    return MAGIC + struct.pack('<31I', *h[1:]) + px.tobytes()

def to_png(pcbytes, path, premult_bg=True):
    from PIL import Image
    h, px = decode_pc(pcbytes)
    rgba = px[..., [2, 1, 0, 3]]
    Image.fromarray(np.ascontiguousarray(rgba), 'RGBA').save(path)
    return rgba

# ---------------- self test / DLC generation ----------------
def _archives():
    from locals import SRC
    from archive import Archive
    return {k: Archive(SRC[k][0], SRC[k][1]) for k in ('xbase', 'xbase2', 'tu', 'pcbig', 'pcpatch')}

def selftest(verbose=False):
    import glob, collections
    from names import crc
    arcs = _archives()
    names = set()
    for f in glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ref', 'yura-release', 'FileLists', 'Tomb Raider Underworld*.txt')):
        for l in open(f, encoding='utf8', errors='ignore'):
            l = l.strip().lower()
            if '\\image\\' in l and l.endswith('.raw'): names.add(l[l.index('image\\'):])
    stat = collections.Counter(); bad = []
    for r in sorted(names):
        def get(prefix, keys):
            for k in keys:
                f = arcs[k].find(crc(prefix + r))
                if f: return arcs[k].read(f[0]), k
            return None, None
        # PC: patch.000 overrides bigfile; Xbox: TU overrides layer1/2. Compare every Xbox variant with every PC variant.
        xs = [(arcs[k].read(f), k) for k in ('xbase', 'xbase2', 'tu') for f in arcs[k].find(crc('xenon-w\\' + r))]
        ps = [(arcs[k].read(f), k) for k in ('pcbig', 'pcpatch') for f in arcs[k].find(crc('pc-w\\' + r))]
        if not xs or not ps: stat['no_pair'] += 1; continue
        px = set(); ok = False; fmts = set()
        for xb, kx in xs:
            try: conv = xbox_to_pc(xb)
            except Exception as e: stat['xbox_decode_error'] += 1; bad.append((r, kx, str(e))); continue
            fmts.add(struct.unpack('>I', xb[12:16])[0])
            for pb, kp in ps:
                if conv == pb: ok = True; stat['exact:%s<-%s' % (kp, kx)] += 1
        if ok: stat['pairs_exact'] += 1
        else: stat['pairs_mismatch'] += 1; bad.append((r, 'mismatch', [len(c) for c, _ in ps], [len(c) for c, _ in xs]))
        for f in fmts: stat['fmt%d' % f] += 1
    return stat, bad

def dlc_gen(outdir):
    import hashlib
    from convert_dlc import PACKS, R
    from archive import Archive
    from names import crc
    os.makedirs(os.path.join(outdir, 'image'), exist_ok=True); os.makedirs(os.path.join(outdir, 'check'), exist_ok=True)
    lines = [l.split() for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work', 'generic', 'dlc_names.txt')) if '\\image\\' in l or 'image' in l]
    # every !WAR record of the 4 DLC packs (named or not)
    recs = {}
    for p in PACKS:
        a = Archive(R + p, 'be')
        for r in a.idx:
            if r['spec'] != 0xffffffff: continue
            b = a.read(r)
            if b[:4] != MAGIC: continue
            recs.setdefault(r['hash'], []).append((p.split('/')[1], b))
    names = {}
    for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work', 'generic', 'dlc_names.txt'), encoding='utf8', errors='ignore'):
        t = l.split()
        if len(t) >= 6 and t[5].startswith('xenon-w\\image'): names[int(t[0], 16)] = t[5]
    out = []; md5 = []
    for h, lst in sorted(recs.items(), key=lambda kv: names.get(kv[0], '~%08x' % kv[0])):
        nm = names.get(h, 'xenon-w\\unnamed\\UNNAMED_%08x.raw' % h)   # name unknown: NOT installable, kept apart
        # same hash may have different content in pack10/pack11 (DLC1 vs DLC2 version): keep the largest (= full image, others are placeholders)
        lst2 = sorted(lst, key=lambda t: -len(t[1]))
        best_pack, best = lst2[0]
        alt = [(p, len(b), hashlib.md5(b).hexdigest()[:8]) for p, b in lst2[1:] if b != best]
        pc = xbox_to_pc(best)
        rel = nm.split('\\', 1)[1]            # image\xxx.raw
        dst = os.path.join(outdir, rel.replace('\\', os.sep)); os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, 'wb').write(pc)
        base = rel.split('\\')[-1][:-4]
        rgba = to_png(pc, os.path.join(outdir, 'check', base + '.png'))
        hh = header(pc, '<')
        flat = len(np.unique(rgba.reshape(-1, 4), axis=0))
        md5.append('%s  %s' % (hashlib.md5(pc).hexdigest(), rel.replace('\\', '/')))
        assert np.array_equal(decode_pc(pc)[1], decode_xbox(best)[1])   # PC file decodes to the same pixels as the Xbox source
        out.append((rel, hh[5], hh[6], len(pc), best_pack, flat, alt))
    open(os.path.join(outdir, 'md5.txt'), 'w').write('\n'.join(md5) + '\n')
    return out

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'selftest':
        st, bad = selftest()
        for k, v in sorted(st.items()): print(k, v)
        for b in bad[:20]: print('BAD', b)
    elif cmd == 'dlc':
        out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work', 'dlc_images')
        for o in dlc_gen(os.path.abspath(out)): print(o)
    elif cmd == 'file':
        pc = xbox_to_pc(open(sys.argv[2], 'rb').read()); open(sys.argv[3], 'wb').write(pc)
        if len(sys.argv) > 4: to_png(pc, sys.argv[4])
    else: print(__doc__)
