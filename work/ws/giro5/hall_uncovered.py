import sys, io, contextlib, struct, json
sys.path.insert(0, '/path/to/trudlcport/work/ws/giro5')
with contextlib.redirect_stdout(io.StringIO()):
    import build_unlit as B
C = B.F14.C; L = B.libs(); DM = L['DM']; D = L['D']; P = L['P']
tree = C.read_tree(B.ROOT + '/work/baseline/B87_materiali19/mods')
secs = {(s.type, s.id): s for s in tree['dlc_caverns_hall.drm'].sections}
sm = json.load(open(B.ROOT + '/work/render/dlc_shader_map.json'))
for (t, mid), s in sorted(secs.items()):
    if t != 10: continue
    l = struct.unpack_from('<4I', s.data, 0x28)
    st = 'COPERTO' if (mid in DM and (9, l[2]) in secs) else 'NO'
    if st == 'NO':
        xl = struct.unpack_from('>4I', DM[mid][0], 0x28) if mid in DM else None
        print(mid, st, 'libPC', l, 'inDM', mid in DM, 'libX', xl, 'cls', [sm.get(str(x), {}).get('cls') for x in (xl or [])])
