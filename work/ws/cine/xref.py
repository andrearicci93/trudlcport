"""xref.py ADDR [ADDR...] -> chiamate/salti diretti e riferimenti a dati (push imm / dword) all'indirizzo nell'exe spacchettato"""
import struct, sys
d = open('work/laa/tru_steam.exe.unpacked.exe', 'rb').read()
pe = struct.unpack_from('<I', d, 0x3c)[0]; ns = struct.unpack_from('<H', d, pe + 6)[0]; osz = struct.unpack_from('<H', d, pe + 20)[0]; ib = struct.unpack_from('<I', d, pe + 52)[0]
secs = []
for i in range(ns):
    o = pe + 24 + osz + 40 * i; vs, va, rs, ra = struct.unpack_from('<IIII', d, o + 8); secs.append((va, vs, ra, rs))
va, vs, ra, rs = secs[0]; code = d[ra:ra + rs]; base = ib + va
def f2v(off):
    for va_, vs_, ra_, rs_ in secs:
        if ra_ <= off < ra_ + rs_: return ib + va_ + off - ra_
for a in sys.argv[1:]:
    t = int(a, 16); calls = []
    for i in range(len(code) - 5):
        if code[i] in (0xe8, 0xe9) and base + i + 5 + struct.unpack_from('<i', code, i + 1)[0] == t: calls.append(hex(base + i))
    refs = []; p = -1; b = struct.pack('<I', t)
    while True:
        p = d.find(b, p + 1)
        if p < 0: break
        refs.append(hex(f2v(p) or 0))
    print(a, 'call/jmp:', calls[:30], '| dati:', refs[:20])
