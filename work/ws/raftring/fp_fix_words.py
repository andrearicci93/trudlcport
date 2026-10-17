"""fp_fix_words.py - applica SOLO le parole 'FP' (dtp_audit) di UN file DLC, con i controlli del protocollo di fix (PIANO §5).
Uso: python -I work/ws/raftring/fp_fix_words.py <setdir rel. a work> <file.drm> <outdir>
Controlli: (1) cambiano solo le parole loggate; (2) idempotente; (3) header/reloc/nomi/sezioni identici; (4) md5 in uscita."""
import sys, os, struct, hashlib
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
import dtp_audit as DA, drm_write as DW, drm_reloc as R
sd, name, out = sys.argv[1:4]
RAWF = '--raw-float-only' in sys.argv
FORMS = None
if '--forms' in sys.argv:
    FORMS = {tuple(l.split()) for l in open(sys.argv[sys.argv.index('--forms') + 1]) if l.strip()}
import struct as _st
def _plaus(h):
    v = _st.unpack('>f', bytes.fromhex(h))[0]; return v == v and v != 0 and 1e-3 <= abs(v) <= 1e7
rel, path = list(DA.overlay(sd.split(','), {name}).items())[0]
xs = DA.xsecs(rel); raw = open(path, 'rb').read(); D = DW.read(raw, 'le'); rl = DA.rules(); logs = []
for x, i in DA.section_pairs(xs, D):
    sec = D.sections[i]
    if x['type'] != 7 or len(sec.data) != len(x['data']): continue
    fr = R.parse(x['reloc'], 'be')
    nb = bytearray(sec.data); slots = set(fr.pointer_offsets()) | set(fr.id_offsets())
    for kind, o, xw, pw, want, got, rule in DA.fp_findings(x['data'], fr, sec.data, rl):
        if kind != 'FP' or o in slots: continue
        if FORMS is not None and (xw, pw, want) not in FORMS: continue
        if RAWF and not (xw == pw and rule == 's32' and _plaus(xw)): continue
        assert bytes(nb[o:o + 4]).hex() == pw
        nb[o:o + 4] = bytes.fromhex(want); logs.append((sec.id, o, xw, pw, want, got, rule))
    sec.data = bytes(nb)
assert logs, 'nessuna parola FP'
o = D.write('le')
if raw[:4] == b'CDRM': o = DW.cdrm_encode(o, 'le')
dst = os.path.join(W := DA.W, out) if not os.path.isabs(out) else out
dst = os.path.join(dst, rel); os.makedirs(os.path.dirname(dst), exist_ok=True); open(dst, 'wb').write(o)
# (2) idempotenza: sul risultato nessuna parola FP restante tra quelle toccate
D2 = DW.read(o, 'le'); D0 = DW.read(raw, 'le'); changed = set()
assert D0.names == D2.names and len(D0.sections) == len(D2.sections)
for a0, a2 in zip(D0.sections, D2.sections):
    assert (a0.type, a0.id, a0.reloc, a0.ver, a0.flags) == (a2.type, a2.id, a2.reloc, a2.ver, a2.flags)   # (3)
    if a0.data != a2.data: changed |= {(a0.id, j - j % 4) for j in range(len(a0.data)) if a0.data[j] != a2.data[j]}
logged = {(l[0], l[1]) for l in logs}
assert changed == logged, (changed ^ logged)                                                               # (1)
for x, i in DA.section_pairs(xs, D2):
    sec = D2.sections[i]
    if x['type'] == 7 and len(sec.data) == len(x['data']):
        again = [f for f in DA.fp_findings(x['data'], R.parse(x['reloc'], 'be'), sec.data, rl) if f[0] == 'FP' and (sec.id, f[1]) in logged]
        assert not again, again
print(rel, 'parole cambiate', len(logs), 'md5', hashlib.md5(o).hexdigest())
for l in logs: print('  DTP %d @0x%x xbox %s pc %s -> %s (era %s, regola %s)' % l)
