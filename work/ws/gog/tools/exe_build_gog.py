#!/usr/bin/env python3
"""exe_build_gog.py - the fork's B138-style tru.exe (LAA + four guards, no title-update code) built from the GOG exe.

The fork's tools/exe_build.py builds the B138 exe from the Steamless-unpacked Steam exe and gates its input by MD5.
The GOG exe is the same image for every byte the guards check (exe_build --check: all sites 'original'), except the
last 16 bytes of .text (0x83dff0..0x83dfff), which are 0x10 padding on GOG and zeros on Steam. The combat-lock guard
puts its code cave over them. This wrapper zeroes those 16 bytes and runs the fork's own stages (build_bytes: each
guard checks its original bytes, applies, verifies with capstone, re-checks) without the Steamless MD5 gates.

  python -I work/ws/gog/tools/exe_build_gog.py GOG_TRU_EXE OUT.exe [--fork DIR]

OUT must not be the input. Exit 0 = all stages passed and OUT written.
"""
import argparse, hashlib, os, sys

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument('exe'); ap.add_argument('out')
ap.add_argument('--fork', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tomb-raider-underworld-dlc-pc'))
a = ap.parse_args()
if os.path.abspath(a.exe) == os.path.abspath(a.out): sys.exit('refused: OUT is the input')
sys.path.insert(0, os.path.join(os.path.abspath(a.fork), 'tools'))
import exe_build as E                               # noqa: E402  (fork tool, unchanged)

GOG_MD5 = '76b4da2fd9178299065bb83412f324ef'
PAD_OFF, PAD_LEN = 0x43dff0, 16                     # file offset of VA 0x83dff0 (.text raw == VA - 0x400000)
d = bytearray(open(a.exe, 'rb').read())
m = hashlib.md5(d).hexdigest()
if m != GOG_MD5: sys.exit('refused: input md5 %s is not the GOG tru.exe %s' % (m, GOG_MD5))
if bytes(d[PAD_OFF:PAD_OFF + PAD_LEN]) != b'\x10' * PAD_LEN: sys.exit('refused: padding bytes differ from the known GOG value')
d[PAD_OFF:PAD_OFF + PAD_LEN] = bytes(PAD_LEN)
st = E.Stages()
out = E.build_bytes(bytes(d), st)
if out is None: sys.exit('a stage refused - nothing written')
open(a.out, 'wb').write(out)
print('written %s  md5 %s  size %d' % (a.out, hashlib.md5(out).hexdigest(), len(out)))
