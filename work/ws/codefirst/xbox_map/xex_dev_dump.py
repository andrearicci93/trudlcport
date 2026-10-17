"""Estrae l'immagine piatta di un XEX2 (cifrato, compressione 'basic') con la chiave retail o devkit (zeri). Uso: xex_dev_dump.py in.xex out.bin"""
import struct, subprocess, sys
d = open(sys.argv[1], 'rb').read()
pe_off = struct.unpack('>I', d[8:12])[0]; si = struct.unpack('>I', d[0x10:0x14])[0]; n = struct.unpack('>I', d[0x14:0x18])[0]
opt = {}
for i in range(n):
    k, v = struct.unpack('>II', d[0x18 + 8 * i:0x20 + 8 * i]); opt[k] = v
ff = opt[0x3ff]; infosz, enc, comp = struct.unpack('>IHH', d[ff:ff + 8])
blocks = [struct.unpack('>II', d[ff + 8 + 8 * j:ff + 16 + 8 * j]) for j in range((infosz - 8) // 8)]
print('pe_off %#x enc %d comp %d blocks %d sum %#x' % (pe_off, enc, comp, len(blocks), sum(a for a, b in blocks)))
fkey_enc = d[si + 0x150:si + 0x160]
def aes(mode, key, iv, data, dec=True):
    a = ['openssl', 'enc', '-d' if dec else '-e', '-aes-128-' + mode, '-K', key.hex(), '-nopad']
    if iv is not None: a += ['-iv', iv.hex()]
    return subprocess.run(a, input=data, capture_output=True, check=True).stdout
RETAIL = bytes([0x20, 0xB1, 0x85, 0xA5, 0x9D, 0x28, 0xFD, 0xC3, 0x40, 0x58, 0x3F, 0xBB, 0x08, 0x96, 0xBF, 0x91])
ok = None
for name, mk in (('retail', RETAIL), ('devkit', bytes(16))):
    fk = aes('ecb', mk, None, fkey_enc)
    head = aes('cbc', fk, bytes(16), d[pe_off:pe_off + 64])
    print(name, head[:16].hex())
    if head[:2] == b'MZ': ok = (name, fk); break
if not ok: sys.exit('chiave non trovata')
plain = aes('cbc', ok[1], bytes(16), d[pe_off:pe_off + sum(a for a, b in blocks)])
out = bytearray(); p = 0
for a, b in blocks: out += plain[p:p + a]; p += a; out += bytes(b)
open(sys.argv[2], 'wb').write(out); print('scritto', len(out), hex(len(out)))
