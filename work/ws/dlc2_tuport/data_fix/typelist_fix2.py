"""typelist_fix2.py - lista di tipi u8 a livello di profilo (filtro P = modo+0x94: P+8 flag, P+0xc n, P+0x10 lista; letta byte per byte
da 0x7232e0, primo filtro del collettore 0x70f300) dei modi 44/46/106/117 (caduta dal ledge) nel DTP 20212 del doppelganger
(18/11/2026, Traccia V). Lista di 19 tipi a 0x80ed0: l'ultima parola (0x80ee0) e' stata convertita come due u16: Xbox 08 15 16 00 ->
PC 15 08 00 16, cosi' il tipo 22 (vena) cade al 20esimo byte, fuori dalla lista, e il distacco dal ledge non trova mai la vena sotto.
Le altre 54 liste di profilo sono identiche all'Xbox. Si applica sopra typelist_fix.py (B272).
uso: typelist_fix2.py --src BASELINE --out DIR [--dry]"""
import sys, os, hashlib
R_ = 'C:/tru-port/'; sys.path.insert(0, R_ + 'tools')
import drm_write as DW
a = sys.argv; SRC = R_ + 'work/baseline/%s/mods/' % a[a.index('--src') + 1]; outd = a[a.index('--out') + 1]; dry = '--dry' in a
OFF = {0x80ee0: ('15080016', '08151600')}
os.makedirs(outd, exist_ok=True); res = {}
for f in ('doppelganger_casual.drm', 'dlc_doppel_costume_a.drm'):
    raw = open(SRC + f, 'rb').read(); D = DW.read(raw, 'le'); hit = [s for s in D.sections if s.type == 7 and s.id == 20212]; assert len(hit) == 1
    b = bytearray(hit[0].data)
    for o, (old, new) in OFF.items():
        old, new = bytes.fromhex(old), bytes.fromhex(new)
        assert bytes(b[o:o + len(old)]) == old, (f, hex(o), b[o:o + len(old)].hex())
        b[o:o + len(new)] = new; print('  ', f, hex(o), '%s -> %s' % (old.hex(), new.hex()))
    hit[0].data = bytes(b); o_ = D.write('le')
    if raw[:4] == b'CDRM': o_ = DW.cdrm_encode(o_, 'le')
    D0 = DW.read(raw, 'le'); D2 = DW.read(o_, 'le'); ch = set()
    for x, y in zip(D0.sections, D2.sections):
        assert (x.type, x.id, x.reloc, len(x.data)) == (y.type, y.id, y.reloc, len(y.data))
        if x.data != y.data: ch |= {(x.id, j - j % 4) for j in range(len(x.data)) if x.data[j] != y.data[j]}
    assert ch == {(20212, o) for o in OFF}, sorted(ch)
    rt = DW.read(o_, 'le').write('le'); rt = DW.cdrm_encode(rt, 'le') if o_[:4] == b'CDRM' else rt; assert rt == o_, 'round-trip'
    if not dry: open(os.path.join(outd, f), 'wb').write(o_)
    res[f] = hashlib.md5(o_).hexdigest(); print(f, len(ch), 'parole')
if not dry: open(os.path.join(outd, 'md5.txt'), 'w').write(''.join('%s  %s\n' % (h, r) for r, h in sorted(res.items())))
print('TOTALE', len(OFF), 'parole in', len(res), 'file')
