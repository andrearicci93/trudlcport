# B61: streamgroups/dlc_water_wheel_waterwheel_main.drm, librerie PS 1086 e 1087 (BackBufferTexture): tutte le entry PS -> output x0.
import sys, os, struct, hashlib
ROOT = '/path/to/trudlcport'
sys.path.insert(0, os.path.join(ROOT, 'tools')); sys.path.insert(0, os.path.join(ROOT, 'work/ws/shader3'))
import drm_write, d3d9_consts, relayout
SRC = os.path.join(ROOT, 'work/baseline/B43/mods/streamgroups/dlc_water_wheel_waterwheel_main.drm')
OUT = os.path.join(ROOT, 'work/ws/shader3/B61/streamgroups/dlc_water_wheel_waterwheel_main.drm')
TARGETS = (1086, 1087)
def rt(r): return ((r >> 28) & 7) | ((r >> 8) & 0x18)
def patch_payload(pl):
    bc_len = relayout.bytecode_len(pl); trailer = pl[bc_len:]
    n = bc_len // 4; t = list(struct.unpack_from('<%dI' % n, pl, 0))
    assert t[0] == 0xffff0300, hex(t[0])
    used, rel = d3d9_consts.used_consts(pl[:bc_len]); k = max(used) + 1
    assert k <= 223 and not rel, (k, rel)
    i = 1; instr = []; first = None
    while i < n:
        tok = t[i]; op = tok & 0xFFFF
        if op == 0xFFFF: break
        if op == 0xFFFE: i += 1 + ((tok >> 16) & 0x7FFF); continue
        ln = (tok >> 24) & 0xF
        if first is None: first = i
        assert not (tok & (1 << 28)), 'predicazione'
        instr.append((i, op, ln)); i += 1 + ln
    end = i                                  # indice del token FFFF
    newt = t[:first] + [0x05000051, 0xA00F0000 | k, 0, 0, 0, 0] + t[first:end] + [0x02000001, 0x800F0800, 0xA0E40000 | k] + t[end:]
    return struct.pack('<%dI' % len(newt), *newt) + trailer
raw = open(SRC, 'rb').read()
d = drm_write.read(raw, 'le')
for s in [x for x in d.sections if x.type == 9 and x.id in TARGETS]:
    assert relayout.relayout_contig(s.data) == s.data, 'round trip %d' % s.id
    tb, _ = struct.unpack_from('<II', s.data, 4)
    slots = list(struct.unpack_from('<%dI' % (tb // 4), s.data, 12))
    offs = sorted(set(x for x in slots if x != 0xffffffff))
    ends = {o: (offs[j + 1] if j + 1 < len(offs) else len(s.data) - 4) for j, o in enumerate(offs)}
    patch = {o: patch_payload(s.data[4 + o + 16:4 + ends[o]]) for o in offs}
    s.data = relayout.relayout_contig(s.data, patch)
    print('lib', s.id, 'entry patchate', len(patch))
out = drm_write.cdrm_encode(d.write('le'), 'le')
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, 'wb').write(out)
print('scritto', OUT, len(out), hashlib.md5(out).hexdigest())
