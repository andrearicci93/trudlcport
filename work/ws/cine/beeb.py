"""Famiglia DTP 'beeb' dei DRM cine (base 3636/3747/10034, DLC 23767): regioni delimitate dai bersagli dei puntatori
interni; classe per (dimensione regione, offset) imparata dalle coppie base Xbox/PC di uguale dimensione."""
import sys, os, struct, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cinepairs
sys.path.insert(0, cinepairs.T)
import drm_reloc as R
def cls(x, p):
    s32 = x[::-1] == p; s16 = x[1::-1] + x[3:1:-1] == p
    if s32 and s16: return 'both'
    if s32: return 's32'
    if s16: return 's16'
    if x == p: return 'raw'
    if x[0:2] + x[3:1:-1] == p: return 'b2s16'   # {u8,u8,u16}
    if x[1::-1] + x[2:4] == p: return 's16b2'
    return 'other'
def regions(d, rel):
    r = R.parse(rel, 'be'); t = sorted({0, len(d)} | {b for a, b in r.internal})
    ptr = {a for a, b in r.internal}; ids = {o for _, o in r.idref}
    return [(a, b) for a, b in zip(t, t[1:])], ptr, ids
def is_beeb(x): return x['data'][8:12] == b'\xbe\xeb\xbe\xeb'
def learn():
    P = cinepairs.load(); tab = collections.defaultdict(collections.Counter); seen = set()
    for n, X, Pp in P:
        for x, p in zip([s for s in X if s['type'] == 7], [s for s in Pp if s['type'] == 7]):
            if not is_beeb(x) or x['size'] != p['size'] or x['data'] in seen: continue
            seen.add(x['data'])
            regs, ptr, ids = regions(x['data'], x['reloc'])
            for a, b in regs:
                for o in range(a, b - 3, 4):
                    if o in ptr or o in ids: continue
                    tab[(b - a, o - a, a == 0)][cls(x['data'][o:o + 4], p['data'][o:o + 4])] += 1
    return tab
if __name__ == '__main__':
    tab = learn()
    sizes = collections.Counter(k[0] for k in tab)
    print('regioni apprese (dimensione:parole)', sorted(sizes.items())[:40])
    amb = [(k, dict(v)) for k, v in tab.items() if len([c for c in v if c not in ('both',)]) > 1]
    print('posizioni contraddittorie', len(amb), 'su', len(tab)); print(amb[:15])
