"""Genera varianti 'bisect' di shader PS del port (rifiutati dal driver nativo) per capire QUALE costrutto fa fallire CreatePixelShader.
Le varianti NON sono semanticamente corrette: servono solo a vedere se il driver le accetta."""
import struct

NODST = {0x00, 0x19, 0x1a, 0x1b, 0x1c, 0x1d, 0x1e, 0x1f, 0x26, 0x27, 0x28, 0x29, 0x2a, 0x2b, 0x2c, 0x2d, 0x2f, 0x30, 0x41, 0x50, 0x51, 0x52, 0x60}
OPEN = {0x28, 0x29, 0x1b, 0x26}; CLOSE = {0x2b, 0x1d, 0x27}

def parse(code):
    d = list(struct.unpack('<%dI' % (len(code) // 4), code)); i = 1; ins = []
    while i < len(d):
        t = d[i]; op = t & 0xffff
        if op == 0xffff: break
        if op == 0xfffe: n = (t >> 16) & 0x7fff; ins.append([op, [], d[i:i + 1 + n], True]); i += 1 + n; continue
        ln = (t >> 24) & 0xf
        ins.append([op, d[i + 1:i + 1 + ln], t, False]); i += 1 + ln
    return d[0], ins

def build(ver, ins):
    w = [ver]
    for op, tok, hdr, raw in ins:
        if raw: w += hdr
        else: w += [(len(tok) << 24) | (hdr & 0xffffff)] + tok
    w.append(0xffff)
    return struct.pack('<%dI' % len(w), *w)

def operands(op, tok):
    """(indice, 'd'|'s') per ogni token operando, saltando i token di indirizzamento relativo."""
    out = []; k = 0; first = op not in NODST
    while k < len(tok):
        t = tok[k]; role = 'd' if (first and k == 0) else 's'
        out.append((k, role))
        k += 2 if (t >> 13) & 1 else 1
    return out

def rt(t): return ((t >> 28) & 7) | (((t >> 11) & 3) << 3)

def transform(ins, abs_=False, neg=False, sat=False, movneg=False):
    res = []
    for op, tok, hdr, raw in ins:
        if raw or op in (0x1f, 0x51, 0x50, 0x52): res.append([op, list(tok), hdr, raw]); continue
        tk = list(tok)
        for k, role in operands(op, tk):
            t = tk[k]
            if role == 'd':
                if sat: t &= ~0x00700000
            else:
                m = (t >> 24) & 0xf
                if abs_ and m in (11, 12): t &= ~0x0f000000
                if neg and m in (1, 2, 8, 9, 12): t = (t & ~0x0f000000) | (0 if m != 12 else 0)
                if movneg and op == 1 and m == 1 and rt(t) == 2: t &= ~0x0f000000
            tk[k] = t
        res.append([op, tk, hdr, raw])
    return res

def truncate(ins, frac):
    """taglia dopo frac delle istruzioni a profondita' 0 e riempie tutti gli oC visti nell'originale con mov oCn, c0."""
    body = [x for x in ins if not x[3]]
    ocs = set()
    for op, tok, hdr, raw in ins:
        if raw or op in (0x1f, 0x51, 0x50, 0x52) or op in NODST: continue
        if rt(tok[0]) == 8: ocs.add(tok[0] & 0x7ff)
    if not ocs: return None
    idx = [k for k, x in enumerate(ins) if not x[3] and x[0] not in (0x1f, 0x51, 0x50, 0x52)]
    target = int(len(idx) * frac); depth = 0; cut = None; cnt = 0
    for k in idx:
        op = ins[k][0]
        if op in OPEN: depth += 1
        if op in CLOSE: depth -= 1
        if op in (0x19, 0x1a, 0x1e, 0x1c): return None
        cnt += 1
        if cnt >= target and depth == 0: cut = k + 1; break
    if cut is None: return None
    keep = [x for x in ins[:cut]]
    for o in sorted(ocs): keep.append([1, [0x80000000 | (0xf << 16) | (1 << 11) | o if False else (0x800f0800 | (o & 0xf)), 0xa0e40000], 1, False])
    # ci serve una def di c0? se mancante non e' definita ma il registro costante e' sempre valido in ps_3_0
    return keep

def variants(code):
    ver, ins = parse(code)
    V = {'orig': ins, 'nomovneg': transform(ins, movneg=True), 'noabs': transform(ins, abs_=True), 'noneg': transform(ins, neg=True),
         'nosat': transform(ins, sat=True), 'nomods': transform(ins, abs_=True, neg=True, sat=True)}
    return ver, V

def trunc_variants(code, fracs):
    ver, ins = parse(code); out = {}
    for f in fracs:
        t = truncate(ins, f)
        if t: out['trunc%02d' % int(f * 100)] = t
    return ver, out

def ninstr(code):
    return sum(1 for x in parse(code)[1] if not x[3] and x[0] not in (0x1f, 0x51, 0x50, 0x52))

def generate(blobs_rej, blobs_acc, outdir):
    """blobs_*: lista (nome, bytes). Sceglie min/mediana/max dei rifiutati e il piu' grande degli accettati."""
    import os
    os.makedirs(outdir, exist_ok=True)
    rs = sorted(blobs_rej, key=lambda b: ninstr(b[1]))
    picks = []
    if rs: picks += [('min', rs[0]), ('med', rs[len(rs) // 2]), ('max', rs[-1])]
    ac = sorted(blobs_acc, key=lambda b: ninstr(b[1]))
    if ac: picks.append(('acc', ac[-1]))
    n = 0
    for tag, (name, code) in picks:
        ver, V = variants(code)
        for vn, ins in V.items():
            if tag == 'acc' and vn not in ('orig',): continue
            open(os.path.join(outdir, 'bis_%s_%s.bin' % (tag, vn)), 'wb').write(build(ver, ins)); n += 1
        fr = [i / 12 for i in range(1, 12)] if tag in ('min', 'med') else [0.25, 0.5, 0.75]
        ver, T = trunc_variants(code, fr)
        for vn, ins in T.items():
            open(os.path.join(outdir, 'bis_%s_%s.bin' % (tag, vn)), 'wb').write(build(ver, ins)); n += 1
        open(os.path.join(outdir, 'bis_%s_SOURCE.txt' % tag), 'w').write(name + '\n')
    return n
