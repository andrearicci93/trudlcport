"""Hybrid DRM for bisecting crashes: take OUR converted base-game DRM and replace sections of the given types by the REAL PC sections
(matched by (type,id) when unique). usage: hybrid.py name.drm ours.drm out.drm TYPE[,TYPE...]   (kind: 12m = mesh only, 12t = terrain only)"""
import sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_write as DW, drm_reloc as R
from rung1 import raw_pc
name, ours, out, types = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4].split(',')
P = DW.read(raw_pc(name), 'le'); O = DW.read(open(ours, 'rb').read(), 'le')
cnt = collections.Counter((s.type, s.id) for s in P.sections)
pm = {(s.type, s.id): s for s in P.sections if cnt[(s.type, s.id)] == 1}
pos0 = {}
p0 = [s for s in P.sections if s.type == 0]
o0 = [i for i, s in enumerate(O.sections) if s.type == 0]
if len(p0) == len(o0): pos0 = {oi: p0[k] for k, oi in enumerate(o0)}
pc_pos0 = {id(s): k for k, s in enumerate(p0)}
def want(s):
    for t in types:
        if t == '12m' and s.type == 12 and s.data[0x10:0x14] == b'Mesh': return True
        if t == '12t' and s.type == 12 and s.data[0x10:0x14] != b'Mesh': return True
        if t.isdigit() and s.type == int(t): return True
    return False
rep = collections.Counter(); secs = []
ocnt = collections.Counter((s.type, s.id) for s in O.sections)
our_idx = {(s.type, s.id): i for i, s in enumerate(O.sections) if ocnt[(s.type, s.id)] == 1}
pc_key = [(s.type, s.id) for s in P.sections]
def remap(reloc):
    r = R.parse(reloc, 'le'); ext = []
    for si, so, do in r.external:
        k = pc_key[si]
        if k[0] == 0 and P.sections[si] in p0: j = o0[p0.index(P.sections[si])]
        else: j = our_idx.get(k) if cnt[k] == 1 else None
        if j is None: rep['ext_unmapped'] += 1; j = si
        ext.append((j, so, do))
    r.external = ext; return R.write(r, 'le')
for oi, s in enumerate(O.sections):
    if s.type == 0 and '0' in types and oi in pos0:
        q = pos0[oi]; secs.append(DW.Section(q.type, q.id, q.data, remap(q.reloc), q.flags, q.ver, q.spec)); rep['replaced0'] += 1; continue
    if want(s) and s.type != 0:
        q = pm.get((s.type, s.id))
        if q is not None:
            secs.append(DW.Section(q.type, q.id, q.data, remap(q.reloc), q.flags, q.ver, q.spec)); rep['replaced'] += 1; continue
        rep['no_pc_match'] += 1
    secs.append(s)
D = DW.Drm(secs, O.names, O.pad, O.ver, O.u0, O.u1)
open(out, 'wb').write(DW.cdrm_encode(D.write('le'), 'le'))
print(name, dict(rep), 'bytes', os.path.getsize(out))
