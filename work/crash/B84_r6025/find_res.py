"""Scansiona TUTTE le voci di pc/bigfile.000 (e patch.000) cercando sezioni DRM con (tipo,id) dati; stampa hash, nome se noto, spec."""
import sys, os, struct
sys.path.insert(0, 'tools'); import drm
from archive import Archive
from names import crc
want = {(10, 3280), (5, 2849), (8, 3280)}
names = {}
for l in open('ref/yura-release/FileLists/Tomb Raider Underworld (PC).txt', errors='ignore'):
    l = l.strip()
    if l: names[crc(l)] = l
for path in ('pc/bigfile.000', 'pc/patch.000'):
    A = Archive(path, 'le'); n = 0
    for r in A.idx:
        try: d = A.read(r)
        except Exception: continue
        if d[:4] not in (b'CDRM',) and not (len(d) > 24 and struct.unpack_from('<i', d, 0)[0] in (19, 21, 22)): continue
        try: secs = drm.sections_with_data(drm.cdrm_decode(d, 'le'), 'le')[1]
        except Exception: continue
        n += 1
        hit = [(s['type'], s['id']) for s in secs if (s['type'], s['id']) in want]
        if hit: print(path, hex(r['hash']), names.get(r['hash'], '?'), 'spec', hex(r['spec']), hit)
    print(path, 'DRM letti', n)
