"""Xbox music (music\\<name>\\<name>.{mus,sam,mul}) -> PC, silent audio.

Learned on the 32 base pairs (Xbox layer1/2 vs PC bigfile), tools/music_convert.py validate:
  .sam : identical on every Xbox base file (4 XMA RIFF test samples, 8512 B) and on PC 4 FSB4 IMA samples (1024 B, only the FSB
         GUID differs per file) -> the PC .sam of a base track is used as-is (DLC .sam are byte-identical to the base Xbox .sam).
  .mus : 'Mus!' header {.., [1] 0x2560, [7] tracks, [9] A, [10] n, [11] B}:
         [0, 0x2560)  common template: per-offset class learned from the pairs (u32 swap / raw / u16-pair; sample-record fields
                      that differ per platform are copied from the base PC files, where all base files agree)
         [0x2560, B)  9 words '=S=ShhS=?' (word 8 = build path 'c:\\t' -> PC 'e:\\t') then raw event bytes
         [B, A)       n u32 offsets (swap)
         [A, end)     per track 0x58-B record 'S=S=SSSSSS===S=SS=====': [0] rate, [1] 0, [2] 2, [3] loop, [4] total samples
  .mul : the cinstream multiplex format with audio blocks only (mul_convert): PC total = round(xbox total / 256) * 256 (same rule
         as the PC files), blocks a_i = floor(i*rate/30/256)*256 up to the total, silent IMA, header float = #blocks - 1.
usage: music_convert.py OUTDIR name [name ...]   (DLC names from pack10/pack11)   |   music_convert.py validate"""
import sys, os, struct, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from archive import Archive
from names import crc
import mul_convert as M
B = '/path/to/'
XB = [B + 'TombRaiderUnderworld_Patched/' + f for f in ('layer1.000', 'layer2.000')]
PCB = B + 'tru-port/pc/bigfile.000'
_A = {}
def arc(p, e):
    if p not in _A: _A[p] = Archive(p, e)
    return _A[p]

def base_pairs():
    names = sorted({l.strip().split('\\')[2] for l in open(B + 'tru-port/ref/yura-release/FileLists/Tomb Raider Underworld (Xenon).txt')
                    if l.lower().startswith('xenon-w\\music\\')})
    out = {}
    for d in names:
        rec = {}
        for e in ('mus', 'sam', 'mul'):
            x = next((a for a in (arc(p, 'be') for p in XB) if a.find(crc('xenon-w\\music\\%s\\%s.%s' % (d, d, e)))), None)
            p = arc(PCB, 'le').find(crc('pc-w\\music\\%s\\%s.%s' % (d, d, e)))
            if x is None or not p: break
            rec[e] = (x.read(x.find(crc('xenon-w\\music\\%s\\%s.%s' % (d, d, e)))[0]), arc(PCB, 'le').read(p[0]))
        else:
            out[d] = rec
    return out

def _cls(a, b):
    s = set()
    if a[::-1] == b: s.add('S')
    if a == b: s.add('=')
    if a[1::-1] + a[:1:-1] == b: s.add('h')
    return s

_T = None
def template(pairs=None):
    """{offset: ('S'|'='|'h') or ('copy', pc_bytes, xbox_bytes)} for [0, 0x2560)"""
    global _T
    if _T is None:
        pairs = pairs or base_pairs()
        T = {}
        for o in range(0, 0x2560, 4):
            obs = [(r['mus'][0][o:o + 4], r['mus'][1][o:o + 4]) for r in pairs.values()]
            inter = set('S=h')
            for a, b in obs: inter &= _cls(a, b)
            if inter: T[o] = 'S' if 'S' in inter else ('=' if '=' in inter else 'h')
            elif len({a for a, b in obs}) == 1 and len({b for a, b in obs}) == 1: T[o] = ('copy', obs[0][1], obs[0][0])
            else: T[o] = None
        _T = T
    return _T

R2 = '=S=ShhS=?'
R4 = 'S=S=SSSSSS===S=SS====='
def _apply(c, w):
    return w[::-1] if c == 'S' else (w[1::-1] + w[:1:-1] if c == 'h' else w)

def convert_mus(x, total, rate=44100):
    h = struct.unpack_from('>16I', x, 0); A, n, Bo = h[9], h[10], h[11]
    assert x[:4] == b'Mus!' and h[1] == 0x2560 and 0x2560 + 36 <= Bo <= A <= len(x), 'unexpected .mus layout'
    out = bytearray(x); T = template(); bad = 0
    for o in range(0, 0x2560, 4):
        c = T.get(o); w = x[o:o + 4]
        if isinstance(c, tuple):
            if w != c[2]: bad += 1
            out[o:o + 4] = c[1] if w == c[2] else w[::-1]
        elif c is None: bad += 1; out[o:o + 4] = w[::-1]
        else: out[o:o + 4] = _apply(c, w)
    for k, c in enumerate(R2):
        o = 0x2560 + 4 * k; w = x[o:o + 4]
        out[o:o + 4] = (b'e' + w[1:] if w[:1] == b'c' else w) if c == '?' else _apply(c, w)
    for o in range(Bo, A, 4): out[o:o + 4] = x[o:o + 4][::-1]
    for t in range((len(x) - A) // 0x58):
        r = A + 0x58 * t
        for k, c in enumerate(R4): out[r + 4 * k:r + 4 * k + 4] = _apply(c, x[r + 4 * k:r + 4 * k + 4])
        struct.pack_into('<III', out, r, rate, 0, 2)
        struct.pack_into('<I', out, r + 16, total)
    return bytes(out), bad

def convert_mul(xm, total=None):
    rate, w1, xt, ch = struct.unpack_from('>4I', xm, 0)
    T = total if total is not None else ((xt + 128) // 256) * 256
    hx = list(struct.unpack_from('>512I', xm, 0)); hx[2] = T
    a = []; i = 0
    while True:
        v = (i * rate // 30 // 256) * 256
        if v >= T: break
        a.append(v); i += 1
    a.append(T)
    hx[14] = struct.unpack('<I', struct.pack('<f', float(len(a) - 2)))[0]
    out = bytearray(struct.pack('<512I', *hx))
    for k in range(len(a) - 1):
        nsm = a[k + 1] - a[k]
        blk = (struct.pack('<hBB', 0, 0, 0) + b'\0' * 32) * ch * (nsm // 64)
        pl = struct.pack('<4I', len(blk), 0, 0, 0) + blk
        out += struct.pack('<4I', 0, len(pl), a[k], 0) + pl
    return bytes(out), T

def validate():
    pairs = base_pairs(); template(pairs)
    st = collections.Counter()
    for d, r in pairs.items():
        xm, pm = r['mus']; xl, pl = r['mul']
        pt = struct.unpack_from('<I', pl, 8)[0]
        om, bad = convert_mus(xm, pt)
        A = struct.unpack_from('>I', xm, 36)[0]
        skip = set()
        for t in range((len(xm) - A) // 0x58): skip |= {A + 0x58 * t, A + 0x58 * t + 4}     # PC re-encode rate / drift word
        wrong = [o for o in range(0, len(xm) // 4 * 4, 4) if o not in skip and om[o:o + 4] != pm[o:o + 4]]
        ol, T = convert_mul(xl)
        OB = M.blocks(ol, '<'); PB = M.blocks(pl, '<')
        st['files'] += 1; st['mus_exact'] += not wrong; st['mus_wrong_words'] += len(wrong)
        st['mul_total_equal'] += T == pt
        st['mul_blocks_equal'] += [(b[1], len(b[3])) for b in OB] == [(b[1], len(b[3])) for b in PB]
        if wrong: print(d, 'mus wrong', [(hex(o), xm[o:o + 4].hex(), om[o:o + 4].hex(), pm[o:o + 4].hex()) for o in wrong[:5]])
    print(dict(st))

if __name__ == '__main__':
    if sys.argv[1] == 'validate': validate(); sys.exit()
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from convert_dlc import R as ROOT, PACKS
    out = sys.argv[1]
    pairs = base_pairs(); template(pairs)
    pc_sam = pairs['l3_chapel_mus_01']['sam'][1]
    xb_sam = pairs['l3_chapel_mus_01']['sam'][0]
    for d in sys.argv[2:]:
        files = {}
        for p in PACKS:
            a = arc(ROOT + p, 'be')
            for e in ('mus', 'sam', 'mul'):
                r = a.find(crc('xenon-w\\music\\%s\\%s.%s' % (d, d, e)))
                if r and e not in files: files[e] = a.read(r[0])
        if len(files) != 3: print(d, 'missing', set(('mus', 'sam', 'mul')) - set(files)); continue
        if files['sam'] != xb_sam: print(d, 'WARNING: .sam differs from the base Xbox .sam -> base PC .sam used anyway')
        ol, T = convert_mul(files['mul'])
        om, bad = convert_mus(files['mus'], T)
        dd = os.path.join(out, 'music', d); os.makedirs(dd, exist_ok=True)
        for e, b in (('mus', om), ('sam', pc_sam), ('mul', ol)): open(os.path.join(dd, '%s.%s' % (d, e)), 'wb').write(b)
        print(d, 'total', T, 'mus template mismatches', bad, 'mul', len(ol))

def convert_streams(out, packs=('pack10',)):
    """audio\\streams\\*.mul of the DLC packs (audio-only multiplex streams: event sounds, stingers, VO) -> silent PC streams.
    Localised VO: the 0xffffffe1 (English + fallback) variant is written as <name>.mul."""
    from convert_dlc import R as ROOT, PACKS
    rows = [l.split() for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work', 'generic', 'dlc_names.txt'))]
    done = set()
    for r in rows:
        if len(r) < 4 or r[1] not in packs or 'audio\\streams' not in r[-1] or not r[-1].endswith('.mul'): continue
        nm = r[-1]
        if nm in done: continue
        a = arc(ROOT + PACKS[['pack10', 'pack11', 'pack1', 'pack2'].index(r[1])], 'be')
        rr = {x['spec']: x for x in a.find(crc(nm))}
        sp = 0xffffffff if 0xffffffff in rr else (0xffffffe1 if 0xffffffe1 in rr else sorted(rr)[0])
        ol, T = convert_mul(a.read(rr[sp]))
        dst = os.path.join(out, *nm.split('\\')[1:]); os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, 'wb').write(ol); done.add(nm)
        print(nm, hex(sp), 'samples', T, 'bytes', len(ol))
