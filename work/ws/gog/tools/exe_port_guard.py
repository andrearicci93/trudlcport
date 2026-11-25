#!/usr/bin/env python3
"""exe_port_guard.py - port single, self-contained guards from upstream's B270 exe onto another tru.exe build.

Each guard is a list of (VA, original bytes, new bytes). Every original is checked first (code sites: the retail
bytes; cave ranges: zeros), nothing is written unless all of them match, and the result is re-read and checked.
The new bytes are upstream's (andrearicci93/trudlcport B270 exe, MIT), copied byte for byte; they are verified
against the B270 exe given with --b270 so a typo cannot slip in.

Guards:
  shakeguard  (F11, pistol-fire crash in DLC 2): tru+0x1ee940 looks up record 0x855a1c (camera shake) and reads
              [[ret+8]+0x5c] without a null test; the doppelganger's weapon has no record -> read at 0x5c.
              B270 jumps from 0x5ee94d and 0x5ee9bc into a 50-byte null guard at 0x83df90..0x83dfc1.

  python -I work/ws/gog/tools/exe_port_guard.py IN.exe OUT.exe --b270 B270.exe --guard shakeguard
"""
import argparse, hashlib, os, sys

BASE = 0x400000
GUARDS = {
    'shakeguard': [
        (0x5ee94d, '8b40088b505c', 'e93ef6240090'),
        (0x5ee9bc, '8b40088b505c', 'e9e7f5240090'),
        (0x83df90, '00' * 50,
         '8b400885c0750731c9e9b709dbff8b505ce9ad09dbff000085c0740f8b400885c074088b505ce9070adbff31c9e9020adbff'),
    ],
}


def off(va): return va - BASE                      # .text raw offset == RVA for this exe (raw 0x1000 = VA 0x401000)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('src'); ap.add_argument('out'); ap.add_argument('--b270', required=True)
    ap.add_argument('--guard', action='append', required=True, choices=sorted(GUARDS))
    a = ap.parse_args()
    if os.path.abspath(a.src) == os.path.abspath(a.out): sys.exit('refused: OUT is the input')
    d = bytearray(open(a.src, 'rb').read()); ref = open(a.b270, 'rb').read()
    for g in a.guard:
        for va, orig, new in GUARDS[g]:
            o, ob, nb = off(va), bytes.fromhex(orig), bytes.fromhex(new)
            if len(ob) != len(nb): sys.exit('%s 0x%x: length mismatch in the table' % (g, va))
            if ref[o:o + len(nb)] != nb: sys.exit('%s 0x%x: table bytes differ from the B270 exe - refused' % (g, va))
            if bytes(d[o:o + len(ob)]) == nb: print('%s 0x%x: already applied' % (g, va)); continue
            if bytes(d[o:o + len(ob)]) != ob: sys.exit('%s 0x%x: input bytes %s are not the expected original - refused' % (g, va, d[o:o + len(ob)].hex()))
    for g in a.guard:
        for va, orig, new in GUARDS[g]:
            o, nb = off(va), bytes.fromhex(new); d[o:o + len(nb)] = nb
            print('%s 0x%x: %d bytes written' % (g, va, len(nb)))
    open(a.out, 'wb').write(d)
    chk = open(a.out, 'rb').read()
    for g in a.guard:
        for va, orig, new in GUARDS[g]:
            if chk[off(va):off(va) + len(bytes.fromhex(new))] != bytes.fromhex(new): sys.exit('re-read check failed at 0x%x' % va)
    print('written %s md5 %s' % (a.out, hashlib.md5(chk).hexdigest()))
    return 0


if __name__ == '__main__':
    sys.exit(main())
