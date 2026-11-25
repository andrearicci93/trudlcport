#!/usr/bin/env python3
"""exe_block_hashes.py - locate where two tru.exe builds differ WITHOUT sharing the files.

Each side runs this on its own exe and shares only the text output: the PE section table plus one MD5 per 4 KiB
block (file offset, VA when the block is inside a section). `--diff A.txt B.txt` then lists the blocks that differ.
Hashes reveal no game content.

Use: compare the GOG tru.exe (76b4da2f...) with the Steamless-unpacked Steam exe (56d1ce2d...), so the GOG exe can
be normalised to the chain input (work/ws/exe_chain) or the chain's md5 gates can be replaced by byte-site checks.

  python -I work/ws/gog/tools/exe_block_hashes.py TRU.exe > blocks_<build>.txt
  python -I work/ws/gog/tools/exe_block_hashes.py --diff blocks_gog.txt blocks_steamless.txt
"""
import hashlib, struct, sys

BLOCK = 0x1000


def dump(path):
    d = open(path, 'rb').read()
    pe = struct.unpack_from('<I', d, 0x3c)[0]; ns = struct.unpack_from('<H', d, pe + 6)[0]
    so = struct.unpack_from('<H', d, pe + 20)[0]; ib = struct.unpack_from('<I', d, pe + 0x34)[0]
    secs = []
    print('# file %s  size %d  md5 %s' % (path.replace('\\', '/').split('/')[-1], len(d), hashlib.md5(d).hexdigest()))
    for i in range(ns):
        e = pe + 24 + so + 40 * i
        nm = d[e:e + 8].rstrip(b'\0').decode('latin1'); vs, va, rs, ro = struct.unpack_from('<IIII', d, e + 8)
        secs.append((nm, va, rs, ro))
        print('# section %-8s va %#08x vsize %#x raw %#x rsize %#x md5 %s' % (nm, ib + va, vs, ro, rs, hashlib.md5(d[ro:ro + rs]).hexdigest()))
    for o in range(0, len(d), BLOCK):
        where = '-'
        for nm, va, rs, ro in secs:
            if ro <= o < ro + rs: where = '%s %#08x' % (nm, ib + va + o - ro)
        print('%#08x %s %s' % (o, hashlib.md5(d[o:o + BLOCK]).hexdigest(), where))


def diff(a, b):
    def load(p):
        return {l.split()[0]: l.rstrip('\n') for l in open(p) if not l.startswith('#')}
    A, B = load(a), load(b)
    n = 0
    for k in sorted(set(A) | set(B), key=lambda x: int(x, 16)):
        if A.get(k, '').split()[1:2] != B.get(k, '').split()[1:2]:
            n += 1; print('differs: %s  |  %s' % (A.get(k, k + ' (missing)'), B.get(k, k + ' (missing)')))
    print('%d block(s) differ' % n)


if __name__ == '__main__':
    if len(sys.argv) == 4 and sys.argv[1] == '--diff': diff(sys.argv[2], sys.argv[3])
    elif len(sys.argv) == 2: dump(sys.argv[1])
    else: sys.exit(__doc__)
