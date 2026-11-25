"""b277_fix.py - (19/11/2026) B277: sei famiglie di parole DLC2 convertite male, dalle regole del fork LukasKurthRocks
(tools/dlc_fixes_build.py passi objfield, playerblock, genintro, idword, fxnode, exttuning), verificate su B276 con gli script di
work/ws/lukas_check/inv/ (objfield_scan, playerblock_scan, genintro_scan2, faults_scan, exttuning_scan). Ogni parola: valore Xbox
atteso, valore PC attuale atteso, nuovo valore; nessun altro byte cambia (verifica parola per parola + round-trip). DLC1: 0 casi.
- objfield: lista equipaggiamento DTP 25270 gear[0] = Xbox 51 (g_pda) lasciato 51 (PC g_tanks); PC g_pda = 48 -> il D-pad dava le bombole.
- playerblock: doppelganger DTP 20212 blocco +0x20ff0: +0x294 4 u8 (tempo lock LT, letti come byte) grezzi; +0x70c id oggetto u16 68 ->
  PC 52 (fx_saving_grab_prompt). Anche nella copia dlc_doppel_costume_a (stesso DTP).
- genintro: header dati intro dei generatori di pozza, +0x30 u16 max vivi / +0x32, +0x38 u16 gruppo / +0x3a (hall02: 1 letto 256).
- idword: id DTP 24900 / 25907 nelle liste oggetto sub-0x32 dei thrall lasciati in ordine Xbox.
- fxnode: id tipo 1 26624 del nodo effetto +0x110 di dlc_fx_goo_machine* lasciato in ordine Xbox.
- exttuning: player_tru_dlc2_extension DTP 22497, tabella targeter 8/9 e coppie K9 splash damage, 10 parole nell'ordine sbagliato.
uso: b277_fix.py --src BASELINE --out DIR [--dry]"""
import sys, os, hashlib, collections
R_ = '/path/to/trudlcport/'; sys.path.insert(0, R_ + 'tools')
import drm_write as DW
from archive import Archive
from dlc_names import PACKS, fcrc
a = sys.argv; SRC = R_ + 'work/baseline/%s/mods/' % a[a.index('--src') + 1]; outd = a[a.index('--out') + 1]; dry = '--dry' in a
BS = chr(92)
GEN = ['dlc2_ceremony_room', 'dlc2_goo_room', 'dlc2_hall_ceremony_goo', 'dlc2_hall_goo_machine', 'dlc2_hall_machine_ceremony',
       'dlc2_machine_room', 'dlc2_treasure_room_cine', 'dlc_level2_start', 'dlc_yggdrasil_end', 'dlc_yggdrasil_hall01', 'dlc_yggdrasil_hall02']
P = []   # (file, file Xbox, dtp, offset, xbox, pc vecchio, pc nuovo, famiglia)
for f in GEN: P.append((f, f, 25270, 0x28, '00330000', '33000000', '30000000', 'objfield'))
for f in ('doppelganger_casual', 'dlc_doppel_costume_a'):
    P += [(f, 'doppelganger_casual', 20212, 0x20ff0 + 0x294, '08000500', '00050008', '08000500', 'playerblock'),
          (f, 'doppelganger_casual', 20212, 0x20ff0 + 0x70c, '00440000', '44000000', '34000000', 'playerblock')]
for f, d, i, w in (('dlc_yggdrasil_hall02', 23100, 0x2150, [(0x30, '00010007', '00010007', '01000700'), (0x38, '00010000', '00000100', '01000000')]),
                   ('dlc2_hall_machine_ceremony', 25591, 0x86e0, [(0x30, '00020002', '00020002', '02000200'), (0x38, '00020000', '00000200', '02000000')]),
                   ('dlc2_machine_room', 25392, 0x124c0, [(0x30, '0005000f', '0f000500', '05000f00')]),
                   ('dlc2_machine_room', 25392, 0x128e0, [(0x30, '0005000f', '0005000f', '05000f00'), (0x38, '00010000', '00000100', '01000000')]),
                   ('dlc2_machine_room', 25392, 0x12d00, [(0x30, '0005000f', '0005000f', '05000f00'), (0x38, '00010000', '00000100', '01000000')])):
    for o, x, old, new in w: P.append((f, f, d, i + o, x, old, new, 'genintro'))
for f, d, x, new in (('viking_thrall_dlc2_', 24425, '00006144', '44610000'), ('viking_thrall_tutorial_dlc2_', 24535, '00006144', '44610000'),
                     ('yeti_thrall_armored_dlc2_', 24889, '00006533', '33650000'), ('yeti_thrall_dlc2_', 24576, '00006533', '33650000')):
    P.append((f, f, d, 0x39c, x, x, new, 'idword'))
for f, d in (('dlc_fx_goo_machine', 22908), ('dlc_fx_goo_machine_a_ist', 22913), ('dlc_fx_goo_machine_b_ist', 26169), ('dlc_fx_goo_machine_c_ist', 26173)):
    P.append((f, f, d, 0x120, '00006800', '00006800', '00680000', 'fxnode'))
for o, x, old, new in ((0x2c0, '08000000', '00000008', '08000000'), (0x2d0, 'ac000000', 'ac000000', '000000ac'), (0x1f0, '00050000', '00050000', '05000000'),
                       (0x204, '00050000', '00000500', '05000000'), (0x220, '00040001', '01000400', '04000100'), (0x224, '42700000', '42700000', '00007042'),
                       (0x25c, '00040001', '00040100', '04000100'), (0x1b0, '0000001a', '0000001a', '1a000000'), (0x1b8, '00000010', '00000010', '10000000'),
                       (0x1bc, '00000016', '00000016', '16000000')):
    P.append(('player_tru_dlc2_extension', 'player_tru_dlc2_extension', 22497, o, x, old, new, 'exttuning'))
A = [Archive(PACKS[p], 'be') for p in ('pack11', 'pack10')]
def xbox(n):
    h = fcrc('xenon-w' + BS + n + '.drm')
    for ar in A:
        rs = [r for r in ar.idx if r['hash'] == h]
        if rs: return ar.read(rs[0])
by = collections.defaultdict(list)
for p in P: by[p[0]].append(p)
fam = collections.Counter(); outs = []
for f, ps in sorted(by.items()):
    raw = open(SRC + f + '.drm', 'rb').read(); D = DW.read(raw, 'le'); plan = set()
    for _, xf, d, o, x, old, new, fm in ps:
        xs = [s for s in DW.read(xbox(xf), 'be').sections if s.type == 7 and s.id == d]; assert len(xs) == 1, (xf, d)
        assert xs[0].data[o:o + 4].hex() == x, (f, d, hex(o), 'xbox', xs[0].data[o:o + 4].hex())
        hs = [i for i, s in enumerate(D.sections) if s.type == 7 and s.id == d]; assert len(hs) == 1, (f, d)
        s = D.sections[hs[0]]; b = bytearray(s.data)
        assert b[o:o + 4].hex() == old, (f, d, hex(o), 'pc', b[o:o + 4].hex())
        b[o:o + 4] = bytes.fromhex(new); s.data = bytes(b); plan.add((hs[0], o)); fam[fm] += 1
    o_ = D.write('le')
    if raw[:4] == b'CDRM': o_ = DW.cdrm_encode(o_, 'le')
    D0 = DW.read(raw, 'le'); D2 = DW.read(o_, 'le'); ch = set()
    for i, (x, y) in enumerate(zip(D0.sections, D2.sections)):
        assert (x.type, x.id, x.reloc, len(x.data)) == (y.type, y.id, y.reloc, len(y.data))
        ch |= {(i, j - j % 4) for j in range(len(x.data)) if x.data[j] != y.data[j]}
    assert len(D0.sections) == len(D2.sections) and ch == plan, (f, sorted(ch ^ plan))
    rt = DW.read(o_, 'le').write('le'); rt = DW.cdrm_encode(rt, 'le') if o_[:4] == b'CDRM' else rt; assert rt == o_, 'round-trip'
    print('%-36s parole %d' % (f + '.drm', len(plan))); outs.append((f + '.drm', o_))
print('famiglie', dict(fam), 'totale', sum(fam.values()), 'file', len(outs))
if not dry:
    os.makedirs(outd, exist_ok=True)
    for rel, o_ in outs: open(os.path.join(outd, rel), 'wb').write(o_)
    with open(os.path.join(outd, 'md5.txt'), 'w', newline='\n') as fo:
        fo.write(''.join('%s  %s\n' % (hashlib.md5(o_).hexdigest(), rel) for rel, o_ in outs))
