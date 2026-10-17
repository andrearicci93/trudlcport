import sys, io, contextlib, struct
sys.path.insert(0, '/path/to/trudlcport/work/ws/giro5')
with contextlib.redirect_stdout(io.StringIO()):
    import build_unlit as B
C = B.F14.C; L = B.libs(); DM = L['DM']
tree = C.read_tree(B.ROOT + '/work/baseline/' + (sys.argv[1]) + '/mods')
want = {int(x) for x in sys.argv[2:]}
for rel, d in sorted(tree.items()):
    for s in d.sections:
        if s.type == 10 and s.id in want:
            pe = C.entries(s.data, s.reloc, 'le'); xe = C.entries(*DM[s.id], 'be') if s.id in DM else None
            print(rel, s.id, 'PClib', struct.unpack_from('<4I', s.data, 0x28), 'Xlib', struct.unpack_from('>4I', DM[s.id][0], 0x28) if xe else None)
            if rel.count('/') == 0 or True:
                for k, e in enumerate(pe):
                    x = xe[k] if xe and k < len(xe) else None
                    print('   e%d PC slot%d t%d f%d tex%d' % (k, e['slot'], e['type'], e['flag'], e['tex']), '| X', None if not x else 'slot%d t%d f%d tex%d' % (x['slot'], x['type'], x['flag'], x['tex']))
            break
