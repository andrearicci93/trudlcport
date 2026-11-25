"""b280_fix.py - (20/11/2026) B280: record MarkUp dei modelli (DTP 0x04c20453, header +0x54 n / +0x58 -> record 0x5c B; +0x2e id,
+0x30 osso, +0x34.. posizione/float) convertiti con l'ordine sbagliato. Regola dal base (work/ws/machine_room/model58_cmp.py, 83 modelli,
297 record): +0x2c = coppia u16 {0, id} (s16), +0x34..+0x54 = s32. Il convertitore ha scritto 13 parole +0x2c come u32 (id letto 0) e
una +0x48 come s16 (-1.0 -> denormale). Casi (markup_scan.py su B279): dlc2_uo_machine_column 25549 (5 id + 1 float, il livello 1
della struttura mobile di machine_room), DLC1 dlc1_uo_pillar_of_doom_a 20472 (3 id), _b 20478 (5 id).
Ogni parola: valore Xbox atteso, valore PC attuale atteso, nuovo = forma della regola; nessun altro byte cambia; round-trip.
uso: b280_fix.py --src BASELINE --out DIR [--dry]"""
import sys, os, hashlib, collections
R_ = '/path/to/trudlcport/'
sys.path.insert(0, R_ + 'work/ws/lukas_check/inv'); sys.path.insert(0, R_ + 'tools')
import inv_common as C, drm_write as DW
a = sys.argv; SRC = R_ + 'work/baseline/%s/mods/' % a[a.index('--src') + 1]; outd = a[a.index('--out') + 1]; dry = '--dry' in a
# (file, DTP, offset nella sezione, xbox, pc vecchio, pc nuovo)
T0 = {'dlc2_uo_machine_column.drm': (25549, 0x1170, [(6, 0x2c, '0000097e'), (6, 0x48, 'bf800000'), (7, 0x2c, '00000a75'), (9, 0x2c, '00000a77'),
                                                      (10, 0x2c, '00000a7a'), (12, 0x2c, '00000a81')]),
      'dlc1_uo_pillar_of_doom_a.drm': (20472, None, [(6, 0x2c, '00000891'), (7, 0x2c, '00000892'), (9, 0x2c, '00000894')]),
      'dlc1_uo_pillar_of_doom_b.drm': (20478, None, [(6, 0x2c, '00000940'), (7, 0x2c, '00000941'), (9, 0x2c, '00000897'),
                                                     (10, 0x2c, '00000898'), (12, 0x2c, '000008a1')])}
import drm_reloc as R
outs = []
for f, (d, T, ws) in sorted(T0.items()):
    raw = open(SRC + f, 'rb').read(); D = DW.read(raw, 'le')
    x = [s for s in DW.read(C.xbox(f), 'be').sections if s.type == 7 and s.id == d]; assert len(x) == 1, f; x = x[0]
    hs = [i for i, s in enumerate(D.sections) if s.type == 7 and s.id == d]; assert len(hs) == 1, f; s = D.sections[hs[0]]
    assert bytes(x.data[:4]) == bytes.fromhex('04c20453') and len(x.data) == len(s.data), f
    tt = dict(R.parse(bytes(x.reloc), 'be').internal)[0x58]; assert T is None or tt == T, (f, hex(tt)); T = tt
    b = bytearray(s.data); plan = set()
    for k, o, xh in ws:
        q = T + 0x5c * k + o; xw = bytes(x.data[q:q + 4]); assert xw.hex() == xh, (f, k, hex(o), xw.hex())
        if o == 0x2c: old, new = xw[::-1], xw[1::-1] + xw[:1:-1]
        else: old, new = xw[1::-1] + xw[:1:-1], xw[::-1]
        assert bytes(b[q:q + 4]) == old, (f, k, hex(o), b[q:q + 4].hex(), old.hex())
        b[q:q + 4] = new; plan.add((hs[0], q))
    s.data = bytes(b)
    o_ = D.write('le')
    if raw[:4] == b'CDRM': o_ = DW.cdrm_encode(o_, 'le')
    D0, D2 = DW.read(raw, 'le'), DW.read(o_, 'le'); ch = set(); assert len(D0.sections) == len(D2.sections)
    for i, (u, v) in enumerate(zip(D0.sections, D2.sections)):
        assert (u.type, u.id, u.reloc, len(u.data)) == (v.type, v.id, v.reloc, len(v.data))
        ch |= {(i, j - j % 4) for j in range(len(u.data)) if u.data[j] != v.data[j]}
    assert ch == plan, (f, sorted(ch ^ plan))
    rt = DW.read(o_, 'le').write('le'); rt = DW.cdrm_encode(rt, 'le') if o_[:4] == b'CDRM' else rt; assert rt == o_, 'round-trip'
    print('%-30s DTP %d parole %d' % (f, d, len(plan))); outs.append((f, o_))
if not dry:
    os.makedirs(outd, exist_ok=True)
    for rel, o_ in outs: open(os.path.join(outd, rel), 'wb').write(o_)
    with open(os.path.join(outd, 'md5.txt'), 'w', newline='\n') as fo:
        fo.write(''.join('%s  %s\n' % (hashlib.md5(o_).hexdigest(), rel) for rel, o_ in outs))
print('file', len(outs), 'scritti' if not dry else '(dry)')
