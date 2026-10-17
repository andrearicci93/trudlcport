"""Cantiere 3b: tutti i materiali (in tutti i DRM della baseline) con una texture 6610 (PC) / equivalente Xbox, con lib Xbox, lib PC, classe."""
import sys, io, contextlib, struct, glob, os, json
sys.path.insert(0, '/path/to/trudlcport/work/ws/giro5')
with contextlib.redirect_stdout(io.StringIO()):
    import build_unlit as B
C = B.F14.C; L = B.libs(); DM = L['DM']
BASE = sys.argv[1] if len(sys.argv) > 1 else 'B87_materiali19'
root = B.ROOT + '/work/baseline/%s/mods' % BASE
sm = json.load(open(B.ROOT + '/work/render/dlc_shader_map.json'))
TEX = {int(x) for x in (sys.argv[2].split(',') if len(sys.argv) > 2 else ['6610'])}
tree = C.read_tree(root)
for rel, d in sorted(tree.items()):
    for s in d.sections:
        if s.type != 10: continue
        try: pe = C.entries(s.data, s.reloc, 'le')
        except Exception: continue
        hit = [(k, e['tex']) for k, e in enumerate(pe) if e['tex'] in TEX]
        xt = []
        if s.id in DM:
            try: xt = [(k, e['tex']) for k, e in enumerate(C.entries(*DM[s.id], 'be'))]
            except Exception: pass
        if hit:
            pl = struct.unpack_from('<4I', s.data, 0x28); xl = struct.unpack_from('>4I', DM[s.id][0], 0x28) if s.id in DM else None
            print(rel, 'mat', s.id, 'PClib', pl, 'Xlib', xl, 'cls', [sm.get(str(x), {}).get('cls') for x in (xl or [])], 'hit', hit, 'xbox_tex', xt)
