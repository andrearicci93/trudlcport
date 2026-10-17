# B60: dlc_caverns.drm, lib PC 975 (pixel), primo entry: ultimo mov oC0,src -> mul oC0,src,c<k>; def c<k>=0 in testa. Output x0.
import sys, os, struct, hashlib
ROOT = '/path/to/trudlcport'
sys.path.insert(0, os.path.join(ROOT, 'tools')); sys.path.insert(0, os.path.join(ROOT, 'work/ws/shader3'))
import drm_write, d3d9_consts, relayout
SRC = os.path.join(ROOT, 'work/baseline/B43/mods/dlc_caverns.drm')
OUT = os.path.join(ROOT, 'work/ws/shader3/B60/dlc_caverns.drm')
LIB = 975
raw = open(SRC, 'rb').read()
d = drm_write.read(raw, 'le')
sec = [s for s in d.sections if s.type == 9 and s.id == LIB]
assert len(sec) == 1
sec = sec[0]
assert relayout.relayout_contig(sec.data) == sec.data, 'round trip lib 975 non identico'
tb, _ = struct.unpack_from('<II', sec.data, 4)
slots = list(struct.unpack_from('<%dI' % (tb // 4), sec.data, 12))
offs = sorted(set(x for x in slots if x != 0xffffffff))
o = offs[0]
pl = sec.data[4 + o + 16:4 + offs[1]]
bc_len = relayout.bytecode_len(pl)
trailer = pl[bc_len:]
n = bc_len // 4
t = list(struct.unpack_from('<%dI' % n, pl, 0))
assert t[0] == 0xffff0300, hex(t[0])
used, rel = d3d9_consts.used_consts(pl[:bc_len])
k = max(used) + 1
assert k <= 223 and not rel, (k, rel)
i = 1; instr = []; first = None
while i < n:
    tok = t[i]; op = tok & 0xFFFF
    if op == 0xFFFF: break
    if op == 0xFFFE: i += 1 + ((tok >> 16) & 0x7FFF); continue
    ln = (tok >> 24) & 0xF
    if first is None: first = i
    assert not (tok & (1 << 28)), 'predicazione non gestita @%d' % i
    instr.append((i, op, ln)); i += 1 + ln
def rt(r): return ((r >> 28) & 7) | ((r >> 8) & 0x18)
cands = [(p, op, ln) for p, op, ln in instr if op == 1 and ln == 2 and rt(t[p + 1]) == 8 and (t[p + 1] & 0x7FF) == 0]
assert cands, 'nessun mov oC0'
p = cands[-1][0]
dst, src = t[p + 1], t[p + 2]
newt = t[:first] + [0x05000051, 0xA00F0000 | k, 0, 0, 0, 0] + t[first:p] + [0x03000005, dst, src, 0xA0E40000 | k] + t[p + 3:]
new_pl = struct.pack('<%dI' % len(newt), *newt) + trailer
print('mov oC0 patchato @token %d, c%d libera, bytecode %d -> %d B, trailer %d B' % (p, k, bc_len, len(newt) * 4, len(trailer)))
new_data = relayout.relayout_contig(sec.data, {o: new_pl})
sec.data = new_data
out = drm_write.cdrm_encode(d.write('le'), 'le')
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, 'wb').write(out)
print('scritto', OUT, len(out), 'md5', hashlib.md5(out).hexdigest(), 'raw', len(raw))
