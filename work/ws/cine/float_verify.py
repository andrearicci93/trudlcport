"""Verifica dei candidati 'raw' di float_fix: per ogni parola, regione (tra bersagli di puntatori interni) che la contiene;
cerca regioni GEMELLE (stessa dimensione) nello stesso DTP e guarda come e' convertita la STESSA posizione nelle gemelle:
 - in quante gemelle e' un float plausibile convertito s32 (prova a favore)
 - in quante e' raw con valore float plausibile in Xbox (stesso errore) / raw non float (campo davvero grezzo = prova contro)
Aggiunge: testo ASCII stampabile della parola (indizio del rilevatore di stringhe del convertitore)."""
import sys, os, struct, json, collections, math
T = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'); sys.path.insert(0, T)
import drm, drm_reloc as R
from wave_swap import raw_dlc
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from float_fix import plaus
L = json.load(open(sys.argv[1])); mods = sys.argv[2]
cache = {}
def get(f, did):
    if f not in cache:
        X = [s for s in drm.sections_with_data(drm.cdrm_decode(raw_dlc(f)[0], 'be'), 'be')[1] if s['type'] == 7]
        P = [s for s in drm.sections_with_data(drm.cdrm_decode(open(os.path.join(mods, f), 'rb').read(), 'le'), 'le')[1] if s['type'] == 7]
        cache[f] = {x['id']: (x, p) for x, p in zip(X, P)}
    return cache[f][did]
out = []
for l in L:
    x, p = get(l['file'], l['dtp']); xd, pd = x['data'], p['data']; o = int(l['off'], 16)
    r = R.parse(x['reloc'], 'be'); tg = sorted({0, len(xd)} | {b for _, b in r.internal})
    a = max(t for t in tg if t <= o); b = min(t for t in tg if t > o); rel = o - a; size = b - a
    sib = [(t, n) for t, n in zip(tg, tg[1:]) if n - t == size and t != a]
    st = collections.Counter()
    for t, n in sib:
        w = xd[t + rel:t + rel + 4]; q = pd[t + rel:t + rel + 4]
        if w == b'\0' * 4: st['zero'] += 1
        elif q == w[::-1] and plaus(w, '>', False): st['float_s32'] += 1
        elif q == w and plaus(w, '>', False): st['float_raw(stesso errore)'] += 1
        elif q == w: st['raw_non_float'] += 1
        else: st['altro'] += 1
    w = bytes.fromhex(l['xbox']); asc = all(32 <= c < 127 for c in w)
    out.append(dict(l, regione=hex(a), dim=size, pos=rel, gemelle=len(sib), stat=dict(st), ascii=asc))
for e in out:
    print('%-28s %5d %8s val=%12.4f reg %s+%d (dim %d, gemelle %d) ascii=%s %s' % (e['file'][:28], e['dtp'], e['off'], e['valore'], e['regione'], e['pos'], e['dim'], e['gemelle'], e['ascii'], e['stat']))
json.dump(out, open(os.path.join(os.path.dirname(sys.argv[1]), 'float_verify.json'), 'w'), indent=1)
