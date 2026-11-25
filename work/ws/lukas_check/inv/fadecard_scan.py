"""fadecard_scan.py - (19/11/2026) solo lettura. Verifica del passo `fadecard` del fork (suo typed_family_fix.py
famiglia fadecard, logica riscritta): DTP fade-record (firma Xbox beebbeeb a +0x08 e +0x48, u16 n a +0x44,
dimensione 0x90 + 12 n): +0x44 {u16 n, u16 0} -> s16; record k a 0x90+12k: {u16 from, u16 to} s16, {u16 frames, u16 w2}
s16, {u8 r,g,b,a} raw. Coppie di sezioni per posizione (difflib su (tipo, dimensione)), stesso id (o id base mappato),
stessa lunghezza. Difetto = parola PC != attesa ma e' un'altra permutazione dei byte Xbox (il fork corregge solo queste);
'kept' = PC non e' permutazione dei byte Xbox. Slot di rilocazione esclusi.
uso: python -I -B fadecard_scan.py BASELINE"""
import sys, os, struct, collections, difflib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, '/path/to/trudlcport/tools')
import inv_common as C, drm_write as DW, drm_reloc as R
BL = sys.argv[1]
L = C.Log(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fadecard_scan_%s.log' % BL.split('_')[0]))
BEEB = b'\xbe\xeb\xbe\xeb'
PERM = {'s32': (3, 2, 1, 0), 's16': (1, 0, 3, 2), 'raw': (0, 1, 2, 3)}
im7 = C.idmap().get(7, {})


def fade_words(xd):
    if len(xd) < 0x9c or xd[8:12] != BEEB or xd[0x48:0x4c] != BEEB: return {}
    n = struct.unpack_from('>H', xd, 0x44)[0]
    if not n or len(xd) != 0x90 + 12 * n: return {}
    out = {0x44: 's16'}
    for k in range(n):
        o = 0x90 + 12 * k; out[o] = 's16'; out[o + 4] = 's16'; out[o + 8] = 'raw'
    return out


def by_position(X, P):
    a = [(s.type, len(s.data)) for s in X]; b = [(s.type, len(s.data)) for s in P]; out = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == 'equal' or (tag == 'replace' and i2 - i1 == j2 - j1 and [t for t, _ in a[i1:i2]] == [t for t, _ in b[j1:j2]]):
            out += [(X[i1 + k], P[j1 + k]) for k in range(j2 - j1)]
    return out


tot = collections.Counter(); seen = set()
for rel, path in C.files(BL):
    xr = C.xbox(rel)
    if xr is None: continue
    X = DW.read(xr, 'be').sections; P = DW.read(open(path, 'rb').read(), 'le').sections
    for x in X:
        if x.type == 7 and fade_words(x.data): tot['DTP fade Xbox (tutte)'] += 1
    for x, p in by_position(X, P):
        if x.type != 7 or p.type != 7 or p.id not in (x.id, im7.get(x.id)) or len(x.data) != len(p.data): continue
        w = fade_words(x.data)
        if not w: continue
        tot['DTP fade accoppiati'] += 1; tot['record'] += (len(w) - 1) // 3
        sl = C.slots(x.reloc, 'be') | C.slots(p.reloc, 'le'); nb = 0
        for o, c in sorted(w.items()):
            if o in sl: tot['parole su slot (saltate)'] += 1; continue
            xw, pw = x.data[o:o + 4], p.data[o:o + 4]; want = bytes(xw[i] for i in PERM[c])
            tot['parole'] += 1
            if pw == want: tot['ok'] += 1; continue
            k = 'DIFETTO' if sorted(xw) == sorted(pw) else 'kept'
            tot[k] += 1; nb += 1
            L('%s %s DTP %d +0x%x %s xbox %s pc %s atteso %s' % (k, rel, p.id, o, c, xw.hex(), pw.hex(), want.hex()))
        L('%s DTP %d: %d record, %d parole non ok' % (rel, p.id, (len(w) - 1) // 3, nb))
L('TOTALE %s' % dict(sorted(tot.items())))
