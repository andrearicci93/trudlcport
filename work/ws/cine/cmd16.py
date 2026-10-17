"""DTP comandi con id iniziale (es. DLC 23766, base 16541): {u32 id DTP} + record da 16 B {tipo,fot}{uid}{msg,par}{w}."""
import sys, os, struct, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cinepairs, beeb
sys.path.insert(0, cinepairs.T)
import drm_reloc as R
P = cinepairs.load()
tab = collections.defaultdict(collections.Counter); ex = []
for n, X, Pp in P:
    for x, p in zip([s for s in X if s['type'] == 7], [s for s in Pp if s['type'] == 7]):
        d, q = x['data'], p['data']
        if x['size'] != p['size'] or len(d) < 20 or d[4] not in (0x10, 0x14, 0x18, 0x20, 0x24, 0x28, 0x40): continue
        r = R.parse(x['reloc'], 'be')
        if not any(o == 0 for _, o in r.idref): continue
        o = 4
        while o + 16 <= len(d):
            t = d[o:o + 2].hex()
            if d[o] not in (0x10, 0x14, 0x18, 0x20, 0x24, 0x28, 0x40): break
            for k in range(4): tab[(t, k)][beeb.cls(d[o + 4 * k:o + 4 * k + 4], q[o + 4 * k:o + 4 * k + 4])] += 1
            o += 16
        ex.append((n, x['id'], len(d), o))
for k in sorted(tab): print(k, dict(tab[k]))
print(len(ex), ex[:8])
