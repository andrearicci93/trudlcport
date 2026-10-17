"""Grafi UberObject: classi delle parole nelle liste azioni dei nodi (NODE+0x18 -> lista) e nei 0x18 B dopo ogni TRANS,
imparate dalle coppie base (pairs_7); confronto con un DTP dell'overlay."""
import sys, os, pickle, collections, struct
T = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'); sys.path.insert(0, T)
import dtp_schema as S, drm_reloc as R
CL = ('s32', 's16', 'raw', 'b2s16', 's16b2')
def conv(w, c): return {'s32': w[::-1], 's16': w[1::-1] + w[3:1:-1], 'raw': w, 'b2s16': w[0:2] + w[3:1:-1], 's16b2': w[1::-1] + w[2:4]}[c]
def regions(xd, xr):
    """[(chiave, offset)]: azioni nodo ('act', k) per k parola della lista; coda dopo TRANS ('tail', k)"""
    r = R.parse(xr, 'be') if isinstance(xr, (bytes, bytearray)) else xr; it = dict(r.internal)
    out = []; targets = sorted(set(it.values()) | {len(xd)})
    for i in S.find_D(xd, r):
        if i.struct == 'NODE' and (i.base + 0x18) in it:
            t = it[i.base + 0x18]; nx = min(x for x in targets if x > t)
            for k in range(0, min(nx - t, 64), 4): out.append((('act', k), t + k))
        if i.struct == 'TRANS':
            t = i.base + 0x28; nx = min(x for x in targets if x >= t) if any(x >= t for x in targets) else len(xd)
            for k in range(0, min(nx - t, 0x18), 4): out.append((('tail', k), t + k))
    return out, {a for a, _ in r.internal} | {o for _, o in r.idref}
if __name__ == '__main__':
    tab = collections.defaultdict(collections.Counter); ex = collections.defaultdict(list); seen = set()
    for q in pickle.load(open(os.path.join(T, '..', 'work', 'script', 'pairs_7.pkl'), 'rb')):
        xd, pd = q['xd'], q['pd']
        if len(xd) != len(pd) or xd in seen: continue
        seen.add(xd)
        try: regs, slots = regions(xd, q['xr'])
        except Exception: continue
        for key, o in regs:
            if o in slots: continue
            s = frozenset(c for c in CL if conv(xd[o:o + 4], c) == pd[o:o + 4])
            tab[key][s] += 1
            if len(s) < 5 and len(ex[key]) < 4: ex[key].append((q['name'].split('\\')[-1][:18], xd[o:o + 4].hex(), pd[o:o + 4].hex()))
    for key in sorted(tab):
        cnt = tab[key]; tot = sum(cnt.values())
        dec = next((c for c in CL if all(c in s for s in cnt)), None)
        print(key, 'campioni', tot, 'regola', dec, {tuple(sorted(s)) if len(s) < 5 else 'ANY': n for s, n in cnt.items()}, ex[key][:3])
