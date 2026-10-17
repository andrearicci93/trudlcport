"""apply_words.py - applica a UN file DRM le parole elencate in un TSV (file,dtp,off,xbox,pc,regola) con la permutazione della regola.
Uso: python -I apply_words.py <setdir rel. work> <rel file> <candidates.tsv> <outdir assoluto>
Controlli: PC attuale == valore registrato; cambiano SOLO le parole elencate; header/reloc/nomi identici; idempotente."""
import sys, os, hashlib
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
import dtp_audit as DA, drm_write as DW
sd, relf, tsv, out = sys.argv[1:5]
P = DA.PERMS
rows = [l.rstrip('\n').split('\t') for l in open(tsv)][1:]
rows = [r for r in rows if r[0] == relf]
assert rows, 'nessuna parola per ' + relf
rel, path = list(DA.overlay([sd], {os.path.basename(relf)}).items())[0]
if rel != relf: rel, path = [(k, v) for k, v in DA.overlay([sd], None).items() if k == relf][0]
raw = open(path, 'rb').read(); D = DW.read(raw, 'le'); logged = set(); log = []
for r in rows:
    dtp, off, xb, pc, rule = int(r[1]), int(r[2], 16), bytes.fromhex(r[3]), bytes.fromhex(r[4]), r[5].split('/')
    assert len(rule) == 1, rule
    want = bytes(xb[j] for j in P[rule[0]])
    sec = [s for s in D.sections if s.id == dtp and s.type == 7][0]
    cur = bytes(sec.data[off:off + 4]); assert cur == pc, (dtp, hex(off), cur.hex(), pc.hex())
    b = bytearray(sec.data); b[off:off + 4] = want; sec.data = bytes(b); logged.add((dtp, off)); log.append((dtp, off, xb.hex(), pc.hex(), want.hex(), rule[0]))
o = D.write('le')
if raw[:4] == b'CDRM': o = DW.cdrm_encode(o, 'le')
dst = os.path.join(out, relf); os.makedirs(os.path.dirname(dst), exist_ok=True); open(dst, 'wb').write(o)
D0 = DW.read(raw, 'le'); D2 = DW.read(o, 'le'); changed = set()
assert D0.names == D2.names and len(D0.sections) == len(D2.sections)
for a0, a2 in zip(D0.sections, D2.sections):
    assert (a0.type, a0.id, a0.reloc, a0.ver, a0.flags) == (a2.type, a2.id, a2.reloc, a2.ver, a2.flags)
    if a0.data != a2.data: changed |= {(a0.id, j - j % 4) for j in range(len(a0.data)) if a0.data[j] != a2.data[j]}
assert changed == logged, changed ^ logged
print(relf, 'parole cambiate', len(log), 'md5', hashlib.md5(o).hexdigest())
for l in log: print('  DTP %d @0x%x xbox %s pc %s -> %s (%s)' % l)
