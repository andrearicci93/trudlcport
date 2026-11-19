"""tgflag_fix.py - machine_room: flag del terrain group 14 (render della sezione 26691, un livello della struttura centrale)
convertito copiando i byte invece di scambiarli (18/11/2026).
DTP 25392 di dlc2_machine_room.drm, blocco dati del gruppo 14 a +0x22420, parola +0x24: Xbox 0x00002000 (u32 BE), PC 00002000
(= 0x00200000 letto LE). I gruppi 13/15 (altri due livelli) hanno 0x4000/0x1000 convertiti bene; i gruppi 1-12, 16-28 hanno 1.
Effetto: il livello 26691 non viene disegnato (collisione presente) -> «muro trasparente» davanti alla cupola.
Scansione di tutti i 190 DRM DLC (tgflag_scan.py): unico caso. Controllo valore vecchio/Xbox, round-trip DRM, nessun altro byte.
uso: tgflag_fix.py --src BASELINE --out DIR [--dry]"""
import sys, os, hashlib
R_ = 'C:/tru-port/'; sys.path.insert(0, R_ + 'tools')
import drm_write as DW
a = sys.argv; SRC = R_ + 'work/baseline/%s/mods/' % a[a.index('--src') + 1]; outd = a[a.index('--out') + 1]; dry = '--dry' in a
F, DTP, OFF, OLD, NEW = 'dlc2_machine_room.drm', 25392, 0x22420 + 0x24, '00002000', '00200000'
X = DW.read(open(R_ + 'work/dlc2/xbox/' + F, 'rb').read(), 'be')
xs = [s for s in X.sections if s.type == 7 and s.id == DTP]; assert len(xs) == 1
assert xs[0].data[OFF:OFF + 4][::-1].hex() == NEW, xs[0].data[OFF:OFF + 4].hex()     # valore Xbox 0x00002000
raw = open(SRC + F, 'rb').read(); D = DW.read(raw, 'le'); hit = [s for s in D.sections if s.type == 7 and s.id == DTP]; assert len(hit) == 1
b = bytearray(hit[0].data); assert b[OFF:OFF + 4].hex() == OLD, b[OFF:OFF + 4].hex()
b[OFF:OFF + 4] = bytes.fromhex(NEW); hit[0].data = bytes(b)
o_ = D.write('le')
if raw[:4] == b'CDRM': o_ = DW.cdrm_encode(o_, 'le')
D0 = DW.read(raw, 'le'); D2 = DW.read(o_, 'le'); ch = set()
for x, y in zip(D0.sections, D2.sections):
    assert (x.type, x.id, x.reloc, len(x.data)) == (y.type, y.id, y.reloc, len(y.data))
    if x.data != y.data: ch |= {(x.id, j - j % 4) for j in range(len(x.data)) if x.data[j] != y.data[j]}
assert ch == {(DTP, OFF)}, sorted(ch)
rt = DW.read(o_, 'le').write('le'); rt = DW.cdrm_encode(rt, 'le') if o_[:4] == b'CDRM' else rt; assert rt == o_, 'round-trip'
print(F, hex(OFF), '%s -> %s' % (OLD, NEW))
if not dry:
    os.makedirs(outd, exist_ok=True); open(os.path.join(outd, F), 'wb').write(o_)
    open(os.path.join(outd, 'md5.txt'), 'w').write('%s  %s\n' % (hashlib.md5(o_).hexdigest(), F))
