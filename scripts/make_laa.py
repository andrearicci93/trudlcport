#!/usr/bin/env python3
"""Set the LARGE_ADDRESS_AWARE bit (0x20 in IMAGE_FILE_HEADER.Characteristics) of a PE file. Never writes the input.
usage: python3 scripts/make_laa.py IN.exe OUT.exe"""
import sys, struct, hashlib
src, dst = sys.argv[1:3]
d = bytearray(open(src, 'rb').read())
pe = struct.unpack_from('<I', d, 0x3C)[0]
assert d[pe:pe + 4] == b'PE\0\0', 'not a PE file'
ch = struct.unpack_from('<H', d, pe + 22)[0]
struct.pack_into('<H', d, pe + 22, ch | 0x20)
open(dst, 'wb').write(d)
print('characteristics %#x -> %#x, md5 %s' % (ch, ch | 0x20, hashlib.md5(d).hexdigest()))
