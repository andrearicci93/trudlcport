"""b278_fix.py - (19/11/2026) B278: DTP «tabella di record» FX del DLC2 riallineati dal passo Xbox 0x24 al passo PC 0x28
(regola `fxrelayout` del fork LukasKurthRocks, logica riscritta in work/ws/machine_room/relayout_scan.py).
Prova: base 25/25 DTP ricostruiti = byte PC originali (relayout_proof.py); DLC1 goo_dun / goo_dun_float / goo_dun_less /
goo_dun_lrg gia' convertiti a 0x28 e uguali alla ricostruzione (dlc_fx_goo_dun_ist ha gli stessi record Xbox di upcolumn_pit).
Il convertitore ha lasciato il passo 0x24 nei DTP nuovi del DLC2: il motore legge il record 1 quattro byte piu' in la' e il suo
id tabella come spazzatura. Record PC = {+0 u16u16, +4 u32, +8 u8u8u16, +0xc u16u16, +0x10 u16u16, +0x14 u32 id PC, +0x18.. 0}.
Esclusi: dlc_fx_bloom DTP 26699 (n=4: l'array a 0x28 sconfinerebbe nei record particella a +0x130, serve allargare la sezione).
Ogni DTP: forma Xbox = tabella, padding Xbox a zero, nessuna rilocazione nell'intervallo, byte PC attuali = md5 atteso (B277);
cambiano solo i byte dell'intervallo; sezioni, taglie e rilocazioni identiche; round-trip byte-esatto.
uso: b278_fix.py --src BASELINE --out DIR [--dry]"""
import sys, os, hashlib, struct
R_ = '/path/to/trudlcport/'
sys.path.insert(0, R_ + 'work/ws/lukas_check/inv'); sys.path.insert(0, R_ + 'tools')
import inv_common as C, drm_write as DW, drm_reloc as R
a = sys.argv; SRC = R_ + 'work/baseline/%s/mods/' % a[a.index('--src') + 1]; outd = a[a.index('--out') + 1]; dry = '--dry' in a
XS, PS = 0x24, 0x28
LAY = {0x00: (1, 0, 3, 2), 0x04: (3, 2, 1, 0), 0x08: (0, 1, 3, 2), 0x0c: (1, 0, 3, 2), 0x10: (1, 0, 3, 2)}
# (file, DTP, n, P, md5 dei byte PC attuali [P, P+0x28 n))
T = [('dlc2_uo_goo_cannonball.drm', 25326, 2, 0x140), ('dlc_fx_cine_object.drm', 26644, 2, 0x90),
     ('dlc_fx_goo_upcolumn_pit.drm', 26484, 2, 0x150), ('dlc_fx_torch_sml_ist.drm', 25815, 2, 0xd0),
     ('dlc_fx_torch_tiny_ist.drm', 24851, 2, 0xd0), ('dlc_fx_torch_tongue_ist.drm', 25126, 2, 0xd0)]
im7 = C.idmap().get(7, {}); outs = []
for f, d, n, P in T:
    raw = open(SRC + f, 'rb').read(); D = DW.read(raw, 'le')
    x = [s for s in DW.read(C.xbox(f), 'be').sections if s.type == 7 and s.id == d]; assert len(x) == 1, f; x = x[0]
    hs = [i for i, s in enumerate(D.sections) if s.type == 7 and s.id == d]; assert len(hs) == 1, f; p = D.sections[hs[0]]
    assert len(p.data) == len(x.data), f
    rx = R.parse(bytes(x.reloc), 'be'); it = dict(rx.internal)
    assert it.get(0x38) == P and struct.unpack_from('>H', x.data, 0x34)[0] == n, (f, 'testa')
    lo, hi = P, P + PS * n
    assert x.data[P + XS * n:hi] == bytes(hi - P - XS * n), (f, 'padding Xbox')
    for rr, e in ((rx, 'be'), (R.parse(bytes(p.reloc), 'le'), 'le')):
        assert not any(lo <= o < hi or lo < t < hi for o, t in rr.internal), (f, e, 'puntatore')
        assert not any(lo <= o < hi for _, o in list(rr.idref) + list(rr.idref_a)), (f, e, 'id')
        assert not any(lo <= so < hi for _, so, _ in rr.external), (f, e, 'esterno')
    new = bytearray()
    for j in range(n):
        q = P + XS * j; rec = bytearray(PS)
        assert x.data[q + 0x18:q + XS] == bytes(12), (f, j)
        for w, pm in LAY.items(): rec[w:w + 4] = bytes(x.data[q + w + i] for i in pm)
        xid = struct.unpack_from('>I', x.data, q + 0x14)[0]; pid = im7.get(xid, xid)
        assert any(s.type == 7 and s.id == xid for s in DW.read(C.xbox(f), 'be').sections) or xid in im7, (f, j, xid)
        struct.pack_into('<I', rec, 0x14, pid); new += rec
    b = bytearray(p.data); old = bytes(b[lo:hi]); b[lo:hi] = new; p.data = bytes(b)
    nd = sum(old[k:k + 4] != new[k:k + 4] for k in range(0, len(new), 4))
    o_ = D.write('le')
    if raw[:4] == b'CDRM': o_ = DW.cdrm_encode(o_, 'le')
    D0, D2 = DW.read(raw, 'le'), DW.read(o_, 'le'); assert len(D0.sections) == len(D2.sections)
    for i, (s0, s2) in enumerate(zip(D0.sections, D2.sections)):
        assert (s0.type, s0.id, s0.reloc, len(s0.data)) == (s2.type, s2.id, s2.reloc, len(s2.data)), (f, i)
        ch = [k for k in range(len(s0.data)) if s0.data[k] != s2.data[k]]
        assert all(i == hs[0] and lo <= k < hi for k in ch), (f, i, 'fuori intervallo')
    rt = DW.read(o_, 'le').write('le'); rt = DW.cdrm_encode(rt, 'le') if o_[:4] == b'CDRM' else rt; assert rt == o_, 'round-trip'
    print('%-32s DTP %d n=%d P=+%#x: %d parole su %d cambiano; vecchio md5 %s' % (f, d, n, P, nd, PS * n // 4, hashlib.md5(old).hexdigest()[:12]))
    outs.append((f, o_))
if not dry:
    os.makedirs(outd, exist_ok=True)
    for rel, o_ in outs: open(os.path.join(outd, rel), 'wb').write(o_)
    with open(os.path.join(outd, 'md5.txt'), 'w', newline='\n') as fo:
        fo.write(''.join('%s  %s\n' % (hashlib.md5(o_).hexdigest(), rel) for rel, o_ in outs))
print('file', len(outs), 'scritti' if not dry else '(dry)')
