"""thrallext_scan.py - (19/11/2026) solo lettura. Verifica del passo `thrallext` del fork (suo thrall_extension_fix.py
modo scan, logica riscritta; regole per campo copiate dalla sua tabella LAYOUT / BSTRUCT_TEXT, che il fork dichiara
provata su istruzioni TU e 209 coppie base Xbox/PC - la prova NON e' rifatta qui).
Oggetto estensione thrall: sezione tipo 7 con radice R = puntatore interno a DTP+0xc8 e u16 R+2 == 0x3d. Header R+0..0x4f,
tabelle: passi (+0x20 ptr, +0x24 n, 0x14 B), record colpo (+0x28 ptr, +0x2c n, 0xc4 B, con struttura reazione 0xb4 a +0x0c
e f32 inserito a +0x40), coppie (+0x30/+0x34, 8 B), rigenerazione (+0x44 ptr, +0x40 n, 0xc B).
Per parola: ordini ammessi (raw/u32/u16x2/u8u8u16/u16u8u8); ok = PC uguale all'unico risultato; DIFETTO (fix:<ordine>)
= PC e' un altro ordine dei byte Xbox; VALUE = nessun ordine (correggibile solo sui campi anim id VALUE_FIX);
UNEXPECTED = nessun ordine su altro campo; UNJUDGED = ordini ammessi danno byte diversi e PC e' uno di essi.
uso: python -I -B thrallext_scan.py BASELINE [--all]"""
import sys, os, struct, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, '/path/to/trudlcport/tools')
import inv_common as C, drm_write as DW, drm_reloc as R
BL = sys.argv[1]; SHOWALL = '--all' in sys.argv
L = C.Log(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'thrallext_scan_%s.log' % BL.split('_')[0]))
ORD = {'raw': (0, 1, 2, 3), 'u32': (3, 2, 1, 0), 'u16x2': (1, 0, 3, 2), 'u8u8u16': (0, 1, 3, 2), 'u16u8u8': (1, 0, 2, 3)}
ALL = frozenset(ORD); U32 = frozenset(['u32']); U16X2 = frozenset(['u16x2']); U8_ = frozenset(['raw', 'u8u8u16'])
U8_U16 = frozenset(['u8u8u16']); U16_ = frozenset(['u16x2', 'u16u8u8'])
HDR, STEP, REC, PAIR, REGEN, BAT, BSZ, RINS = 0x50, 0x14, 0xc4, 8, 0xc, 0x0c, 0xb4, 0x40
LAYOUT = {'h+00': U16X2, 'h+04': U16_, 'h+08': ALL, 'h+0c': U8_, 'h+10': U16X2, 'h+14': U16X2, 'h+18': U8_, 'h+1c': U8_,
          'h+20': U32, 'h+24': U32, 'h+28': U32, 'h+2c': U32, 'h+30': U32, 'h+34': U32, 'h+38': U8_U16, 'h+3c': U16_,
          'h+40': U32, 'h+44': U32, 'h+48': U32, 'h+4c': ALL, 's+00': U16X2, 's+04': U16X2, 's+08': U32, 's+0c': U32,
          's+10': U8_, 'r+00': U32, 'r+04': U8_, 'r+08': U32, 'r+40': U32, 'p+00': U32, 'p+04': U32,
          'g+00': U32, 'g+04': U32, 'g+08': U32}
BT = {}
for o in range(0, 0x14, 4): BT['b+%02x' % o] = U16X2
for o in (0x14, 0x18) + tuple(range(0x20, 0x3c, 4)): BT['b+%02x' % o] = U32
BT['b+1c'] = frozenset(['raw', 'u8u8u16'])
for base in (0x50, 0x78, 0xa0):
    for o in range(base, base + 0x10, 4): BT['b+%02x' % o] = ALL - U32
CODE_TIE = {'b+14': 'u32', 'b+1c': 'raw', 'b+34': 'u32'}
VALUE_FIX = {'h+38', 'h+3c', 'h+10', 'h+14', 's+00', 's+04'}


def perm(w, p): return bytes(w[i] for i in p)
def orders_of(xw, pw): return frozenset(n for n, p in ORD.items() if perm(xw, p) == pw)
def orders_for(k): return BT.get(k, ALL) if k.startswith('b+') else LAYOUT[k]


def judge(k, xw, pw):
    c = orders_for(k); outs = {perm(xw, ORD[q]) for q in c}
    want = next(iter(outs)) if len(outs) == 1 else (perm(xw, ORD[CODE_TIE[k]]) if k in CODE_TIE and CODE_TIE[k] in c else None)
    if want is not None and pw == want: return 'ok', want
    od = orders_of(xw, pw)
    if want is None: return ('UNJUDGED' if od else 'UNEXPECTED'), None
    if od: return 'fix:' + '/'.join(sorted(od)), want
    return ('VALUE' if k in VALUE_FIX else 'UNEXPECTED'), want


class S:
    def __init__(s, sec, e):
        s.id, s.d, s.E = sec.id, sec.data, ('>' if e == 'be' else '<')
        r = R.parse(sec.reloc, e); s.it = dict(r.internal); s.sl = set(r.pointer_offsets()) | set(r.id_offsets())
    def u32(s, o): return struct.unpack_from(s.E + 'I', s.d, o)[0]


def ext_root(s):
    b = s.it.get(0xc8)
    if b is None or b + HDR > len(s.d): return None
    return b if struct.unpack_from(s.E + 'H', s.d, b + 2)[0] == 0x3d else None


def rec_key(o):
    if o < BAT: return 'r+%02x' % o
    if o < RINS: return 'b+%02x' % (o - BAT)
    if o == RINS: return 'r+%02x' % o
    return 'b+%02x' % (o - BAT - 4)


def ext_words(s, b):
    out = [('h+%02x' % o, b + o) for o in range(0, HDR, 4)]
    def table(po, co, esz, kf):
        p = s.it.get(b + po); n = s.u32(b + co)
        if p is None or not 0 < n < 0x100 or p + n * esz > len(s.d): return 0 if p is None and n == 0 else None
        for j in range(n):
            for o in range(0, esz, 4): out.append((kf(o), p + j * esz + o))
        return n
    cnt = dict(steps=table(0x20, 0x24, STEP, lambda o: 's+%02x' % o), records=table(0x28, 0x2c, REC, rec_key),
               pairs=table(0x30, 0x34, PAIR, lambda o: 'p+%02x' % o), regen=table(0x44, 0x40, REGEN, lambda o: 'g+%02x' % o))
    return out, cnt


tot = collections.Counter()
for rel, path in C.files(BL):
    xr = C.xbox(rel)
    if xr is None: continue
    XD = DW.read(xr, 'be').sections; PD = DW.read(open(path, 'rb').read(), 'le').sections
    xs = [S(s, 'be') if s.type == 7 and s.data else None for s in XD]
    ps = [S(s, 'le') if s.type == 7 and s.data else None for s in PD]
    lay = collections.defaultdict(list)
    for k, s in enumerate(ps):
        if s is not None: lay[len(s.d), tuple(sorted(s.it.items()))].append(k)
    used = set()
    for x in xs:
        if x is None or ext_root(x) is None: continue
        cand = [k for k in lay.get((len(x.d), tuple(sorted(x.it.items()))), []) if k not in used]
        same = [k for k in cand if ps[k].id == x.id]
        k = same[0] if same else (cand[0] if len(cand) == 1 else None)
        if k is None: tot['UNPAIRED'] += 1; L('UNPAIRED %s DTP %d' % (rel, x.id)); continue
        used.add(k); p = ps[k]; b = ext_root(x)
        if ext_root(p) != b: tot['LAYOUT'] += 1; L('LAYOUT %s DTP %d radice PC %s' % (rel, x.id, ext_root(p))); continue
        words, cnt = ext_words(x, b)
        if None in cnt.values(): tot['LAYOUT'] += 1; L('LAYOUT %s DTP %d conteggi %s' % (rel, x.id, cnt)); continue
        tot['sezioni estensione'] += 1; nb = collections.Counter()
        for key, o in words:
            if o in x.sl or o in p.sl:
                if (o in x.sl) != (o in p.sl): tot['LAYOUT'] += 1; L('LAYOUT %s DTP %d +0x%x rilocazione su un lato' % (rel, x.id, o))
                continue
            xw, pw = x.d[o:o + 4], p.d[o:o + 4]; stt, want = judge(key, xw, pw)
            tot['parole'] += 1; c = 'ok' if stt == 'ok' else 'DIFETTO' if stt.startswith('fix:') else stt
            tot[c] += 1; nb[c] += 1
            if c != 'ok' or SHOWALL:
                L('  %s %s DTP %d +0x%x %s xbox %s pc %s atteso %s [%s]' % (c, rel, p.id, o, key, xw.hex(), pw.hex(), want.hex() if want else '-', stt))
        L('%s DTP %d->%d radice +0x%x %s: %s' % (rel, x.id, p.id, b, cnt, dict(nb)))
L('TOTALE %s' % dict(sorted(tot.items())))
