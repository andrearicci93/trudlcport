"""Estrae dalla compose (mods reali del candidato) il bytecode PS di ogni slot delle lib 2775-2782 -> work/ws/giro7/valid/lib<ID>_s<k>.bin
(una copia per lib; verifica che le copie nei vari DRM siano identiche). Per vm_ps_validate.ps1 / vm_ps_draw.ps1."""
import sys, os, hashlib
sys.path.insert(0, '/path/to/trudlcport/work/ws/contratti'); sys.path.insert(0, '/path/to/trudlcport/tools')
import contract as C
mods = sys.argv[1]; out = sys.argv[2]; os.makedirs(out, exist_ok=True)
t = C.read_tree(mods); seen = {}; n = 0
for rel, d in sorted(t.items()):
    for s in d.sections:
        if s.type == 9 and 2775 <= s.id <= 2782:
            h = hashlib.md5(s.data).hexdigest()
            if s.id in seen: assert seen[s.id] == h, ('copie diverse', s.id, rel); continue
            seen[s.id] = h; f = C.frame_lib(s.data); assert not f['errors']
            for k, o in enumerate(f['slots']):
                if o == 0xFFFFFFFF: continue
                open('%s/lib%d_s%d.bin' % (out, s.id, k), 'wb').write(f['entries'][o]['bc']); n += 1
print('lib', sorted(seen), 'bin', n)
