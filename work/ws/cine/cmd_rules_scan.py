"""Regole per (formato, tipo record, indice parola) con 0 eccezioni sulle coppie base (pairs_7 + cine) e loro applicazione
all'overlay: elenca le parole dei DTP-comandi DLC che l'overlay ha diverse dalla regola provata."""
import sys, os, pickle, collections, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cine_cmd as CC, cinepairs
sys.path.insert(0, cinepairs.T)
import drm, drm_reloc as R
from wave_swap import raw_dlc

def records(d, ptrs):
    """[(offset parola, chiave)] dello stream comandi fino al terminatore (chiave = (fmt, tipo, k)); None se non torna"""
    f = CC.fmt_of(d)
    if f is None: return None
    o = 4 if f == 'B' else 0; out = []
    if f == 'B': out.append((0, (f, 'id', 0)))
    while o + 4 <= len(d):
        t = struct.unpack_from('>H', d, o)[0]
        if t == 0xffff: out.append((o, (f, 'term', 0))); return out
        c = d[o] >> 4
        if d[o] & 3 or c not in (1, 2, 3, 4): return None
        n = (12 if f == 'A' else 8) + 4 * c
        if o + n > len(d): return None
        for k in range(n // 4): out.append((o + 4 * k, (f, t, k)))
        o += n
    return out if f == 'A' and o == len(d) else None

CL = ('s32', 's16', 'raw', 'b2s16', 's16b2')
def conv(w, c): return {'s32': w[::-1], 's16': w[1::-1] + w[3:1:-1], 'raw': w, 'b2s16': w[0:2] + w[3:1:-1], 's16b2': w[1::-1] + w[2:4]}[c]

def learn():
    tab = collections.defaultdict(collections.Counter); seen = set()
    src = [(q['xd'], q['xr'], q['pd']) for q in pickle.load(open(os.path.join(cinepairs.T, '..', 'work', 'script', 'pairs_7.pkl'), 'rb'))]
    for n, X, P in cinepairs.load():
        src += [(x['data'], x['reloc'], p['data']) for x, p in zip([s for s in X if s['type'] == 7], [s for s in P if s['type'] == 7])]
    for xd, xr, pd in src:
        if len(xd) != len(pd) or xd in seen: continue
        seen.add(xd); r = R.parse(xr, 'be'); slots = {a for a, _ in r.internal} | {o for _, o in r.idref}
        rec = records(xd, slots)
        if not rec: continue
        for o, key in rec:
            if o in slots: continue
            tab[key][frozenset(c for c in CL if conv(xd[o:o + 4], c) == pd[o:o + 4])] += 1
    rules = {}
    for key, cnt in tab.items():
        tot = sum(cnt.values())
        for c in CL:
            if all(c in s for s in cnt):             # compatibile con TUTTI i campioni
                if tot >= 3 and any(len(s) < len(CL) for s in cnt): rules[key] = (c, tot)
                break
    return rules, tab

if __name__ == '__main__':
    rules, tab = learn()
    print('chiavi', len(tab), 'regole provate (0 eccezioni, >=3 campioni)', len(rules))
    mods = sys.argv[1]; diffs = collections.Counter(); rows = []; nodlc = 0
    for f in sorted(os.listdir(mods)):
        if not f.endswith('.drm'): continue
        xr, _ = raw_dlc(f)
        if xr is None: continue
        X = [s for s in drm.sections_with_data(drm.cdrm_decode(xr, 'be'), 'be')[1] if s['type'] == 7]
        P = [s for s in drm.sections_with_data(drm.cdrm_decode(open(os.path.join(mods, f), 'rb').read(), 'le'), 'le')[1] if s['type'] == 7]
        if len(X) != len(P): continue
        for x, p in zip(X, P):
            xd = x['data']
            if len(xd) != len(p['data']): continue
            r = R.parse(x['reloc'], 'be'); slots = {a for a, _ in r.internal} | {o for _, o in r.idref}
            rec = records(xd, slots)
            if not rec: continue
            bad = []
            for o, key in rec:
                if o in slots or key not in rules or key[1] == 'id' or key[2] == 1: continue   # uid/id: valori rimappati
                c = rules[key][0]
                if conv(xd[o:o + 4], c) != p['data'][o:o + 4]: bad.append((hex(o), key, c, xd[o:o + 4].hex(), p['data'][o:o + 4].hex()))
            if bad:
                rows.append((f, x['id'], p['id'], len(bad), bad[:3])); diffs['dtp'] += 1; diffs['parole'] += len(bad)
    print(dict(diffs))
    for r in rows: print('  ', r)
