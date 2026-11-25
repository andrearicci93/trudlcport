"""trusave.py - (20/11/2026) lettore dei salvataggi TRU PC (*.TRUSave). Formato dal fork LukasKurthRocks (tools/trusave_info.py,
tools/trusave_diff.py, ENGINE.md 6.2-6.4), logica riscritta. Funzioni pure: nessuna scrittura (la scrittura e' in trusave_reset.py).
Contenitore: 'RGMH' (testata 0x2028) -> 'PCUD' {+0x10 n voci, +0x14 CRC tabella, +0x18 CRC testata}, tabella n x {size, off, CRC dati};
CRC-32/BZIP2. Dati (0x140000 B) = SaveInfo: arena di blocchi {u32 head = id | (size>>2)<<8; payload} fino a [0x1357f4];
id 6 gioco, 1 unit (+4 chiave unit), 2 extra istanza (+8 uid), 3 istanza con spline (+4 unit corrente, +8 oggetto, +0xc unit di
nascita, +0x10 genitore, +0x14 uid), 4 istanza (+4 unit di nascita, +0x10 genitore, +0x14 uid), 5 istanza piccola (+8 uid).
Dead bits a 0x1357f8 (0x7fc B, bit = uid). Stickies: bool bit 0x135ff4 / id 0x1361f4, int valori 0x13e1f8 / id 0x13e9f8,
float valori 0x13f9fc / id 0x13fbfc; id = u32 n + n x {u32 owner, u16 key, u8 kind, u8}; kind 0 owner = uid intro, 1 = unit.
uso: trusave.py SAVE [UNIT_ID]   (stampa CRC, blocchi, dead bits e stickies; con UNIT_ID e --uids FILE filtra)"""
import struct, sys
DATA = 0x140000; ARENA_END = 0x1357f4; DEAD, DEADLEN = 0x1357f8, 0x7fc
STORES = {'bool': (0x1361f4, 0x135ff4), 'int': (0x13e9f8, 0x13e1f8), 'float': (0x13fbfc, 0x13f9fc)}
UIDOFF = {2: 8, 3: 0x14, 4: 0x14, 5: 8, 1: 4}
_T = []
def crc(b):
    if not _T:
        for i in range(256):
            c = i << 24
            for _ in range(8): c = ((c << 1) ^ 0x04C11DB7) & 0xffffffff if c & 0x80000000 else (c << 1) & 0xffffffff
            _T.append(c)
    c = 0xffffffff
    for x in b: c = ((c << 8) & 0xffffffff) ^ _T[(c >> 24) ^ x]
    return c ^ 0xffffffff
def container(d):
    hs = struct.unpack_from('<I', d, 8)[0] if d[:4] == b'RGMH' else 0
    magic, ver, game, gver, n, tcrc, hcrc = struct.unpack_from('<4sI4sIIII', d, hs)
    t = hs + 0x1c; ents = [struct.unpack_from('<III', d, t + 12 * k) for k in range(n)]
    ok = dict(header=crc(d[hs:hs + 0x18]) == hcrc, table=crc(d[t:t + 12 * n]) == tcrc,
              data=[crc(d[o:o + s]) == c for s, o, c in ents])
    return hs, t, ents, ok
def data_of(d):
    hs, t, ents, ok = container(d)
    s, o, c = next(e for e in ents if e[0] == DATA); return o, ok
def blocks(d, base):
    end = struct.unpack_from('<I', d, base + ARENA_END)[0]; p = 0; out = []
    while p < end:
        h = struct.unpack_from('<I', d, base + p)[0]; bid = h & 0xff; size = (h >> 8) << 2
        if size < 4 or bid not in (1, 2, 3, 4, 5, 6): out.append((p, bid, size, None, 'ROTTO')); break
        u = struct.unpack_from('<I', d, base + p + UIDOFF[bid])[0] if bid in UIDOFF else None
        unit = None
        if bid == 3: unit = struct.unpack_from('<I', d, base + p + 0xc)[0]
        elif bid == 4: unit = struct.unpack_from('<I', d, base + p + 4)[0]
        elif bid == 1: unit = u
        out.append((p, bid, size, u, unit)); p += size
    return out, end
def dead(d, base):
    b = d[base + DEAD:base + DEAD + DEADLEN]
    return {i * 8 + k for i, x in enumerate(b) if x for k in range(8) if x >> k & 1}
def stickies(d, base):
    out = []
    for kind, (ido, vo) in STORES.items():
        n = struct.unpack_from('<I', d, base + ido)[0]
        for k in range(n):
            owner, key, ok_, _ = struct.unpack_from('<IHBB', d, base + ido + 4 + 12 * k)
            if kind == 'bool': v = d[base + vo + (k >> 3)] >> (k & 7) & 1
            elif kind == 'int': v = struct.unpack_from('<i', d, base + vo + 4 * k)[0]
            else: v = struct.unpack_from('<f', d, base + vo + 4 * k)[0]
            out.append((kind, k, owner, key, ok_, v))
    return out
if __name__ == '__main__':
    d = open(sys.argv[1], 'rb').read(); base, ok = data_of(d)
    print('CRC', ok, 'dati a', hex(base))
    bl, end = blocks(d, base)
    import collections
    print('blocchi', len(bl), 'fine arena', hex(end), collections.Counter(b[1] for b in bl))
    print('dead bits', len(dead(d, base)), 'stickies', collections.Counter(s[0] for s in stickies(d, base)))
