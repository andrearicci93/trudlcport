"""Scansione: blocchi dati dei terrain group (0x30 byte; +0x10 = float 75,100,20) nei DTP dei DRM DLC del PC (baseline) contro
l'originale Xbox (pack10/pack11). Riporta le parole +0x20..+0x2c che non sono lo scambio a 32 bit dell'Xbox (la +0x00 grezza e' corretta,
come nei livelli nativi del PC). Solo lettura. uso: python -I -B tgflag_scan.py BASELINE"""
import sys, os, struct, re
sys.path.insert(0, 'C:/tru-port/tools')
import drm_write as DW
from archive import Archive
from dlc_names import PACKS, fcrc
B = 'C:/tru-port/work/baseline/%s/mods/' % sys.argv[1]
A = [Archive(PACKS[p], 'be') for p in ('pack11', 'pack10')]
BS = chr(92)
SIG = bytes.fromhex('4296000042c8000041a00000')
def xbox(rel):
    h = fcrc('xenon-w' + BS + rel.replace('/', BS))
    for a in A:
        rs = [r for r in a.idx if r['hash'] == h]
        if rs: return a.read(rs[0])
tot = 0; files = 0
for root, _, fs in os.walk(B):
    for f in fs:
        if not f.endswith('.drm'): continue
        rel = os.path.relpath(os.path.join(root, f), B).replace(BS, '/')
        xr = xbox(rel)
        if xr is None: continue
        try: X = DW.read(xr, 'be').sections; P = DW.read(open(os.path.join(root, f), 'rb').read(), 'le').sections
        except Exception as e: print('ERR', rel, e); continue
        if len(X) != len(P): continue
        files += 1
        for i, (x, p) in enumerate(zip(X, P)):
            if x.type != 7 or len(x.data) != len(p.data): continue
            for m in re.finditer(re.escape(SIG), x.data):
                o = m.start() - 0x10
                if o < 0 or o + 0x30 > len(x.data): continue
                for j in range(0x20, 0x30, 4):
                    a, b = x.data[o + j:o + j + 4], p.data[o + j:o + j + 4]
                    if a[::-1] != b:
                        tot += 1; print('%s sez %d DTP %d blocco %#x +%#x Xbox %s PC %s atteso %s' % (rel, i, x.id, o, j, a.hex(), b.hex(), a[::-1].hex()))
print('file confrontati', files, 'parole sbagliate', tot)
