"""Per ogni DRM di una baseline: materiali (tipo 10) le cui texture referenziate (idref tipo 5) NON sono nello stesso DRM.
Confronto B73 vs B84: elenca i riferimenti 'esterni' nuovi. Uso: mat_texrefs.py B73 B84"""
import sys, os, struct, collections
sys.path.insert(0, 'tools'); import drm, drm_reloc as R
def scan(B):
    M = 'work/baseline/%s/mods' % B; out = {}
    for root, _, fs in os.walk(M):
        for n in fs:
            if not n.endswith('.drm'): continue
            p = os.path.join(root, n); rel = os.path.relpath(p, M).lower()
            try: secs = drm.sections_with_data(drm.cdrm_decode(open(p, 'rb').read(), 'le'), 'le')[1]
            except Exception: continue
            tex = {s['id'] for s in secs if s['type'] == 5}
            for s in secs:
                if s['type'] != 10 or not s['data']: continue
                r = R.parse(s['reloc'], 'le')
                refs = {struct.unpack_from('<I', s['data'], o)[0] for t, o in r.idref_a + r.idref if t == 5}
                miss = sorted(refs - tex)
                out[(rel, s['id'])] = (tuple(sorted(refs)), tuple(miss))
    return out
a, b = scan(sys.argv[1]), scan(sys.argv[2])
nuovi = [(k, b[k]) for k in b if b[k][1] and (k not in a or set(b[k][1]) - set(a[k][1]))]
print('materiali con texture fuori dal proprio DRM: %s %d, %s %d' % (sys.argv[1], sum(1 for v in a.values() if v[1]), sys.argv[2], sum(1 for v in b.values() if v[1])))
print('NUOVI in', sys.argv[2], len(nuovi))
for (rel, mid), (refs, miss) in sorted(nuovi): print('  %-55s mat %5d  mancanti %s   (prima: %s)' % (rel, mid, list(miss), a.get((rel, mid), ((), ('assente',)))[1]))
