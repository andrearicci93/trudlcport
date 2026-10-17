import sys, io, contextlib, struct
sys.path.insert(0, '/path/to/trudlcport/tools'); sys.path.insert(0, '/path/to/trudlcport/work/ws/giro5')
import drm_write as DW, drm_reloc as R, material_reslot as MR
ROOT = '/path/to/trudlcport'
d = DW.read(open(ROOT + '/work/baseline/B87_materiali19/mods/dlc_caverns.drm', 'rb').read(), 'le')
S = d.sections
idx = {(s.type, s.id): i for i, s in enumerate(S)}
m = S[idx[(10, 23173)]]
rel = R.parse(m.reloc, 'le')
print('external (off, sec_idx?, ...) esempio:', rel.external[:12])
print('entries:', [(hex(o), tid, ty, slot) for o, tid, ty, slot in MR.tex_entries(m.data, rel, '<')])
for o, tid, ty, slot in MR.tex_entries(m.data, rel, '<'):
    hits = [e for e in rel.external if e[0] in (o, o + 4, o + 8, o + 12)]
    print(hex(o), tid, 'reloc esterni sull entry:', hits, '| sezione texture', tid, 'indice', idx.get((5, tid)))
print('indice (5,255):', idx.get((5, 255)), '(5,121):', idx.get((5, 121)), '(5,6549):', idx.get((5, 6549)))
t = S[idx[(5, 255)]] if (5, 255) in idx else None
if t: print('tex 255: len', len(t.data), 'reloc', t.reloc[:16].hex() if t.reloc else None, 'flags/ver/spec/pad', t.flags, t.ver, t.spec, t.pad, 'data head', t.data[:64].hex())
