import sys, io, contextlib, struct
sys.path.insert(0, '/path/to/trudlcport/work/ws/giro5')
with contextlib.redirect_stdout(io.StringIO()):
    import build_unlit as B
C = B.F14.C; DM = B.libs()['DM']
tree = C.read_tree(B.ROOT + '/work/baseline/' + sys.argv[1] + '/mods')
rel, mid = sys.argv[2], int(sys.argv[3]); n = int(sys.argv[4], 0) if len(sys.argv) > 4 else 0x90
s = {(x.type, x.id): x for x in tree[rel].sections}[(10, mid)]
x = DM[mid][0]
for o in range(0, n, 16):
    a = struct.unpack_from('>4I', x, o); b = struct.unpack_from('<4I', s.data, o)
    print('%03x X %s | PC %s %s' % (o, ' '.join('%08x' % v for v in a), ' '.join('%08x' % v for v in b), '' if a == b else '  <-- diverso(endian)'))
