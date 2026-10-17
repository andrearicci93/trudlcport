"""Trova le sezioni (mods B84 e bigfile base) che contengono la firma dei dati materiale letti in memoria."""
import sys, os
sys.path.insert(0, 'tools'); import drm
from archive import Archive
from names import crc
SIG = [bytes.fromhex(x) for x in ('86F80E394E2C108E', 'A27055E2F3C0D55F', 'C07B2A3C9138DDDA')]
def check(label, raw):
    try: secs = drm.sections_with_data(drm.cdrm_decode(raw, 'le'), 'le')[1]
    except Exception: return
    for s in secs:
        d = s['data']
        if d and all(x in d for x in SIG): print(label, 'tipo', s['type'], 'id', s['id'], 'len', len(d), 'off', d.find(SIG[0]))
M = 'work/baseline/B84/mods'
for root, _, fs in os.walk(M):
    for n in fs:
        if n.endswith('.drm'): check(os.path.relpath(os.path.join(root, n), M), open(os.path.join(root, n), 'rb').read())
names = {crc(l.strip()): l.strip() for l in open('ref/yura-release/FileLists/Tomb Raider Underworld (PC).txt', errors='ignore') if l.strip()}
A = Archive('pc/bigfile.000', 'le')
for r in A.idx:
    try: d = A.read(r)
    except Exception: continue
    if d[:4] == b'CDRM' or d[:4] == b'\x13\0\0\0' or d[:4] == b'\x16\0\0\0': check('BASE ' + names.get(r['hash'], hex(r['hash'])), d)
