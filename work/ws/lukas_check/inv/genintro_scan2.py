"""genintro_scan.py - (19/11/2026) solo lettura. Regola dal fork (tools/generator_intro_fix.py, passo genintro), solo header:
dati intro dei generatori di pozza: blocco con parole rilocate a +0x28 e +0x64 che puntano entrambe a +0x70, count 1..16 a +0x70.
Tipi header: +0x30 u16 max vivi, +0x32 u16, +0x34 s16 limite, +0x36 u16, +0x38 u16 gruppo, +0x3a u16, +0x3c..+0x58 f32,
+0x5c u16 flag (bit0 = spawn automatico spento), +0x5e u16, +0x68 f32. Atteso PC = Xbox nell'ordine LE del campo.
Sezioni abbinate per posizione (stessa dimensione e rilocazioni interne). uso: python -I -B genintro_scan.py BASELINE"""
import sys, os, struct, collections
sys.path.insert(0, '/path/to/trudlcport/tools')
import drm_write as DW, drm_reloc as R
from archive import Archive
from dlc_names import PACKS, fcrc
B = '/path/to/trudlcport/work/baseline/%s/mods/' % sys.argv[1]
A = [Archive(PACKS[p], 'be') for p in ('pack11', 'pack10')]; BS = chr(92)
def xbox(rel):
    h = fcrc('xenon-w' + BS + rel.replace('/', BS))
    for a in A:
        rs = [r for r in a.idx if r['hash'] == h]
        if rs: return a.read(rs[0])
U16 = [0x30, 0x32, 0x34, 0x36, 0x38, 0x3a, 0x5c, 0x5e]; F32 = list(range(0x3c, 0x5c, 4)) + [0x68]
def fields():
    for o in range(0x30, 0x3c, 4): yield o, 'u16u16'
    for o in F32: yield o, 'f32'
    yield 0x5c, 'u16u16'
def expect(xb, k):
    return xb[::-1] if k == 'f32' else xb[1::-1] + xb[3:1:-1]
st = collections.Counter()
for root, _, fs in os.walk(B):
    for f in sorted(fs):
        if not f.endswith('.drm'): continue
        rel = os.path.relpath(os.path.join(root, f), B).replace(BS, '/'); xr = xbox(rel)
        if xr is None: continue
        try: X = DW.read(xr, 'be').sections; P = DW.read(open(os.path.join(root, f), 'rb').read(), 'le').sections
        except Exception as e: print('ERR', rel, e); continue
        if len(X) == len(P): prs = list(zip(X, P))
        else:   # numero di sezioni diverso: coppia per forma (stesso tipo, id, dimensione, rilocazioni interne), unica
            st['file_sezioni_diverse'] += 1; prs = []
            for x in X:
                if not x.reloc: continue
                c = [p for p in P if p.type == x.type and p.id == x.id and len(p.data) == len(x.data) and p.reloc]
                if len(c) == 1: prs.append((x, c[0]))
        for x, p in prs:
            if not x.reloc or len(x.data) != len(p.data) or not p.reloc: continue
            xi = dict(R.parse(x.reloc, 'be').internal)
            if xi != dict(R.parse(p.reloc, 'le').internal): continue
            for b in [o - 0x28 for o, t in xi.items() if t == o - 0x28 + 0x70]:
                if xi.get(b + 0x64) != b + 0x70 or b + 0x74 > len(x.data): continue
                n = struct.unpack_from('>I', x.data, b + 0x70)[0]
                if not 1 <= n <= 16: continue
                st['generatori'] += 1; bad = []
                for o, k in fields():
                    xw, pw = x.data[b + o:b + o + 4], p.data[b + o:b + o + 4]
                    if pw != expect(xw, k): bad.append('+0x%x %s xbox %s pc %s' % (o, k, xw.hex(), pw.hex()))
                st['parole_sbagliate'] += len(bad)
                print('%s %s sez %d id %d intro +0x%x n=%d maxvivi xbox %d pc-legge %d flag5c xbox %04x pc %04x  %s' % (
                    'BAD' if bad else 'ok ', rel, x.type, x.id, b, n, struct.unpack_from('>H', x.data, b + 0x30)[0],
                    struct.unpack_from('<H', p.data, b + 0x30)[0], struct.unpack_from('>H', x.data, b + 0x5c)[0],
                    struct.unpack_from('<H', p.data, b + 0x5c)[0], '; '.join(bad)))
print('TOTALE', dict(st))
