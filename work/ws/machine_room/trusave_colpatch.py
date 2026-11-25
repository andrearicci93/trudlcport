"""trusave_colpatch.py - (20/11/2026) COPIA di un salvataggio con la parte 0 della colonna di machine_room portata allo stato finale.
Nel blocco tipo 4 della colonna (intro 11688) ci sono 3 sotto-record (firma 2207a77976fd), uno per parte (indice a +0x43: 0/1/2).
Le parti 1-2 sono nella posa finale (indice anim 3 = 6485), la parte 0 al 2o stadio (indice 2 = 6484). Copia nella parte 0 i byte
[+0x18, +0x2c) e [+0x44, +0x48) della parte 1 (indici animazione, 8 byte di stato, stato 0002 -> 0001); il resto (indice di parte) resta.
Ricalcola i CRC; verifica che cambino solo quei byte (piu' CRC). uso: trusave_colpatch.py IN OUT [--min]   (--min: solo i due byte dell indice animazione 2 -> 3; Savegame 7 senza --min ha fatto crashare il gioco)"""
import sys
sys.path.insert(0, '/path/to/trudlcport/work/ws/machine_room')
import struct, trusave as T
IN, OUT = [x for x in sys.argv[1:] if not x.startswith("--")][:2]; assert IN != OUT
src = open(IN, 'rb').read(); d = bytearray(src); base, ok = T.data_of(src); assert ok['header'] and ok['table'] and all(ok['data'])
bl, _ = T.blocks(src, base)
b = [x for x in bl if x[1] == 4 and x[3] == 11688]; assert len(b) == 1; p0 = base + b[0][0]; B = src[p0:p0 + b[0][2]]
sig = bytes.fromhex('2207a77976fd'); pos = []; i = B.find(sig)
while i >= 0: pos.append(i); i = B.find(sig, i + 1)
assert len(pos) == 3, pos
idx = {B[p + 0x43]: p for p in pos}; assert set(idx) == {0, 1, 2}, idx
a, f = idx[0], idx[1]
assert B[a + 0x1b] == 2 and B[f + 0x1b] == 3 and B[a + 0x23] == 2 and B[f + 0x23] == 3, 'stato inatteso'
assert B[idx[2] + 0x18:idx[2] + 0x2c] == B[f + 0x18:f + 0x2c], 'parti 1 e 2 non uguali'
ranges = [(0x1b, 0x1c), (0x23, 0x24)] if "--min" in sys.argv else [(0x18, 0x2c), (0x44, 0x48)]
for lo, hi in ranges: d[p0 + a + lo:p0 + a + hi] = B[f + lo:f + hi]
hs, t, ents, _ = T.container(src); k = next(j for j, e in enumerate(ents) if e[0] == T.DATA); size, off, _ = ents[k]
struct.pack_into('<I', d, t + 12 * k + 8, T.crc(bytes(d[off:off + size]))); n = struct.unpack_from('<I', d, hs + 0x10)[0]
struct.pack_into('<I', d, hs + 0x14, T.crc(bytes(d[t:t + 12 * n]))); struct.pack_into('<I', d, hs + 0x18, T.crc(bytes(d[hs:hs + 0x18])))
out = bytes(d); b2, ok2 = T.data_of(out); assert ok2['header'] and ok2['table'] and all(ok2['data'])
ch = [i for i in range(len(src)) if src[i] != out[i]]
allowed = [(p0 + a + lo, p0 + a + hi) for lo, hi in ranges] + [(hs + 0x14, hs + 0x1c), (t, t + 12 * n)]
assert all(any(lo <= i < hi for lo, hi in allowed) for i in ch), [hex(i) for i in ch]
open(OUT, 'wb').write(out)
print('parte 0 @blocco+%#x: %s -> %s | byte cambiati %d (CRC compresi) -> %s' % (a, B[a + 0x18:a + 0x2c].hex(), B[f + 0x18:f + 0x2c].hex(), len(ch), OUT))
