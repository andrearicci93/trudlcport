"""exttuning_scan.py - (19/11/2026) solo lettura. Regola riscritta dal fork (tools/player_ext_tuning_fix.py +
tools/tuning_target_fix.py, passo exttuning): player_tru_dlc2_extension.drm DTP 22497, struttura tuning a +0xf0 ({u16 1, u16 60}):
tabella parametri targeter 8/9 (46 parole: u32 / u8+3 zeri / u16u16 / f32) e tabella coppie K9 splash damage (tuning +0x78 ptr,
+0x7c conteggio, voci {s32 from, s32 to}). Atteso PC = byte Xbox nell'ordine little-endian del campo.
uso: python -I -B exttuning_scan.py BASELINE"""
import sys, struct
sys.path.insert(0, '/path/to/trudlcport/tools')
import drm_write as DW, drm_reloc as R
from archive import Archive
from dlc_names import PACKS, fcrc
B = '/path/to/trudlcport/work/baseline/%s/mods/' % sys.argv[1]
NAME = 'player_tru_dlc2_extension.drm'; SID = 22497; BASE = 0xf0
F = [(BASE + 0x94, 'u32'), (0x2c0, 'u8x'), (0x2c8, 'u8x'), (0x2d0, 'u32'), (0x2d4, 'u32'), (0x2dc, 'u32'), (0x2e0, 'u32'),
     (0x294, 'u32'), (0x298, 'u32'), (0x2a8, 'u32'), (0x2ac, 'u32')]
for r in [0x1f0, 0x204, 0x220, 0x234, 0x248, 0x25c, 0x270]:
    F += [(r, 'u16u16'), (r + 4, 'f32'), (r + 8, 'f32'), (r + 0xc, 'f32'), (r + 0x10, 'f32')]
def expect(xb, k):
    if k in ('u32', 'f32'): return xb[::-1]
    if k == 'u16u16': return xb[1::-1] + xb[3:1:-1]
    if k == 'u8x': return xb[:1] + b'\0\0\0' if xb[1:] == b'\0\0\0' else None
h = fcrc('xenon-w' + chr(92) + NAME); xr = None
for p in ('pack11', 'pack10'):
    a = Archive(PACKS[p], 'be'); rs = [r for r in a.idx if r['hash'] == h]
    if rs: xr = a.read(rs[0]); break
sx = next(s for s in DW.read(xr, 'be').sections if s.type == 7 and s.id == SID)
sp = next(s for s in DW.read(open(B + NAME, 'rb').read(), 'le').sections if s.type == 7 and s.id == SID)
xd, pd = bytes(sx.data), bytes(sp.data)
xin, pin = dict(R.parse(sx.reloc, 'be').internal), dict(R.parse(sp.reloc, 'le').internal)
print('size', len(xd), len(pd), 'reloc uguali', xin == pin, 'tuning', struct.unpack_from('>HH', xd, BASE))
cnt = BASE + 0x7c; F.append((cnt, 'u32')); tab = xin.get(BASE + 0x78); n = struct.unpack_from('>i', xd, cnt)[0]
print('K9 tabella', hex(tab) if tab is not None else None, 'n', n)
if tab is not None and 0 < n <= 64:
    for k in range(n): F += [(tab + 8 * k, 'u32'), (tab + 8 * k + 4, 'u32')]
bad = 0
for off, k in F:
    xw, pw = xd[off:off + 4], pd[off:off + 4]; w = expect(xw, k)
    st = 'ok' if pw == w else 'SBAGLIATA'
    if st != 'ok': bad += 1
    print('%s +0x%03x %-6s xbox %s pc %s atteso %s' % (st, off, k, xw.hex(), pw.hex(), w.hex() if w else None))
print('parole controllate %d, sbagliate %d' % (len(F), bad))
