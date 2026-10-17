import sys, os, hashlib
sys.path.insert(0, '/path/to/trudlcport/tools')
import model_point_fix as M, drm_write as DW, dtp_audit as DA
W = M.W
rel = 'dlc1_uo_dragon_slider.drm'
src = os.path.join(W, 'mods_dlc1_rc', rel)
raw = open(src, 'rb').read()
D0 = DW.read(raw, 'le')
raw2, D, logs = M.file_fixes(rel, src)
tp = [l for l in logs if l[2] == 'TP']
other = [l for l in logs if l[2] != 'TP']
print('TP words', len(tp), 'other(not applied)', len(other))
# re-apply only TP: reload and patch by section id/offset
D = DW.read(raw, 'le'); sec = {s.id: s for s in D.sections}
lines = []
for (pid, xid, kind, off, e, old, new, perm) in tp:
    s = sec[pid]; d = bytearray(s.data)
    assert d[off:off+4].hex() == old
    d[off:off+4] = bytes.fromhex(new); s.data = bytes(d)
    lines.append('DTP %d (xbox %d) %s @0x%x elem 0x%x : %s -> %s (rule %s)' % (pid, xid, kind, off, e, old, new, perm))
o = D.write('le')
if raw[:4] == b'CDRM': o = DW.cdrm_encode(o, 'le')
out = os.path.join(W, 'ws/dslider/out'); os.makedirs(out, exist_ok=True)
open(os.path.join(out, rel), 'wb').write(o)
open(os.path.join(out, 'md5.txt'), 'w').write('%s  %s\n' % (hashlib.md5(o).hexdigest(), rel))
open(os.path.join(out, 'fix_log.txt'), 'w').write('\n'.join(lines) + '\nNOT applied (HS words, not target point): ' + str(len(other)) + '\n')
print('\n'.join(lines))
# diff check
D2 = DW.read(open(os.path.join(out, rel), 'rb').read(), 'le')
D0 = DW.read(raw, 'le')
assert D0.names == D2.names and len(D0.sections) == len(D2.sections)
ch = []
for a, b in zip(D0.sections, D2.sections):
    assert (a.type, a.id, a.reloc, a.ver, a.flags) == (b.type, b.id, b.reloc, b.ver, b.flags)
    assert len(a.data) == len(b.data)
    ch += [(a.id, j) for j in range(len(a.data)) if a.data[j] != b.data[j]]
print('changed bytes', ch)
