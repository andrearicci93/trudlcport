"""typelist_fix.py - liste di tipi markup (u8) dei filtri dei profili di movimento nel DTP 20212 del doppelganger, convertite come
parole a 32/16 bit invece che come byte (18/11/2026, Traccia V).
Struttura: modo -> +0x94/+0x9c filtro P {+0x14 n voci, +0x18 voci}; voce {+0x14 flag, +0x18 n tipi, +0x1c lista u8}. Il PC legge la
lista byte per byte (0x723330: movsx byte [lista+i]) e la confronta con TypeOf(markup). Su 117 liste 9 hanno i byte rigirati: il tipo
22 (vena) finisce in coda alla parola e viene letto 0. Effetto: il modo 107 (stato 0x439, «afferra la vena in caduta») e i modi
44/45/46/106/117 non accettano mai le vene; anche 23 e 2 perdono il loro posto.
Regola: per ognuna delle 9 liste, i byte del PC tornano identici all'Xbox (dati u8, indipendenti dall'endianness). Controllo del vecchio
valore e del valore Xbox, round-trip DRM, nessun altro byte cambiato.
uso: typelist_fix.py --src BASELINE --out DIR [--dry]"""
import sys, os, hashlib
R_ = 'C:/tru-port/'; sys.path.insert(0, R_ + 'tools')
import drm_write as DW
a = sys.argv; SRC = R_ + 'work/baseline/%s/mods/' % a[a.index('--src') + 1]; outd = a[a.index('--out') + 1]; dry = '--dry' in a
# offset nel DTP 20212: (byte PC attuali, byte Xbox), regione arrotondata a 4 byte
OFF = {0x7efb0: ('080e0016', '0e081600'), 0x7f020: ('1011121300001614', '1011121314160000'), 0x7f060: ('00000016', '16000000'),
       0x7f5b0: ('00000016', '16000000'), 0x7f5e0: ('00000016', '16000000'), 0x7f740: ('00000002', '02000000'),
       0x7ff00: ('00000016', '16000000'), 0x800c0: ('00001609', '09160000'), 0x801e0: ('00000017', '17000000')}
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
    exp = {(20212, o + k) for o, (old, new) in OFF.items() for k in range(0, len(bytes.fromhex(old)), 4)
           if bytes.fromhex(old)[k:k + 4] != bytes.fromhex(new)[k:k + 4]}
    assert ch == exp, sorted(ch)
    rt = DW.read(o_, 'le').write('le'); rt = DW.cdrm_encode(rt, 'le') if o_[:4] == b'CDRM' else rt; assert rt == o_, 'round-trip'
    if not dry: open(os.path.join(outd, f), 'wb').write(o_)
    res[f] = hashlib.md5(o_).hexdigest(); print(f, len(ch), 'parole')
if not dry: open(os.path.join(outd, 'md5.txt'), 'w').write(''.join('%s  %s\n' % (h, r) for r, h in sorted(res.items())))
print('TOTALE', len(OFF), 'liste in', len(res), 'file')
