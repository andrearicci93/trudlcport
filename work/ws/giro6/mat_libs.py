"""Giro 6: per i materiali indicati, in ogni DRM della dir MODS: tupla lib PC (+0x28), presenza di ciascuna lib nel DRM, tupla Xbox, uso."""
import sys, io, contextlib, struct, collections
sys.path.insert(0, '/path/to/trudlcport/work/ws/giro5')
with contextlib.redirect_stdout(io.StringIO()):
    import build_unlit as B
C = B.F14.C; L = B.libs(); DM = L['DM']
tree = C.read_tree(sys.argv[1]); want = {int(x) for x in sys.argv[2:]}
for rel, d in sorted(tree.items()):
    ids9 = {s.id for s in d.sections if s.type == 9}
    for s in d.sections:
        if s.type == 10 and s.id in want:
            pl = struct.unpack_from('<4I', s.data, 0x28)
            xl = struct.unpack_from('>4I', DM[s.id][0], 0x28) if s.id in DM else None
            print('%-52s mat %d PC %s in-DRM %s | Xbox %s' % (rel, s.id, pl, [x in ids9 for x in pl], xl))
