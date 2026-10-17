"""DTP effetti 'beeb' (header {0,0,ptr,{n u16,0},ptr->n record da 0x17c fino alla fine, ...}): classi per parola imparate dalle
coppie base Xbox/PC di uguale dimensione (work/script/pairs_7.pkl + cinestream), etichetta per parola:
  ('rec', off % 0x17c)                    dentro il vettore di record
  ('reg', etichetta del puntatore, off)  dentro una regione puntata (etichetta = campo header o ('rec', off) della sorgente)
  ('hdr', off)                            campi dell'header prima della prima regione
Uso: fxdtp.py   (impara, valida leave-one-out, stampa copertura sul DLC 23767)"""
import sys, os, pickle, collections, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cinepairs, beeb
sys.path.insert(0, cinepairs.T)
import drm_reloc as R
W = os.path.join(cinepairs.T, '..', 'work')
REC = 0x17c

def is_fx(d): return len(d) >= 0x40 and d[4:8] == b'\0' * 4 and d[8:12] == b'\xbe\xeb\xbe\xeb'

def labels(d, rel):
    r = R.parse(rel, 'be')
    it = dict(r.internal); ptr = set(it); ids = {o for _, o in r.idref}
    n = struct.unpack_from('>H', d, 0xc)[0]; b0 = it.get(0x10)
    if b0 is None or b0 + n * REC != len(d): return None
    lab = {}
    for o in range(b0, len(d) - 3, 4): lab[o] = ('rec', (o - b0) % REC)
    tg = sorted({t for t in it.values() if t < b0} | {b0})
    src = collections.defaultdict(list)
    for a, t in it.items(): src[t].append(a)
    for t, nx in zip(tg, tg[1:]):
        a = min(src.get(t, [None]), key=lambda v: (v is None, v if v is not None else 0))
        if a is None: key = ('?',)
        elif a < tg[0]: key = ('hdr', a)
        elif a >= b0: key = ('rec', (a - b0) % REC)
        else: key = ('sub', a - max(x for x in tg if x <= a))
        for o in range(t, nx, 4): lab[o] = ('reg', key, o - t)
    for o in range(0, tg[0], 4): lab[o] = ('hdr', o)
    return lab, ptr, ids

def samples():
    out = []; seen = set()
    for q in pickle.load(open(os.path.join(W, 'script', 'pairs_7.pkl'), 'rb')):
        if is_fx(q['xd']) and len(q['xd']) == len(q['pd']) and q['xd'] not in seen:
            seen.add(q['xd']); out.append((q['name'], q['xd'], q['xr'], q['pd']))
    for n, X, P in cinepairs.load():
        for x, p in zip([s for s in X if s['type'] == 7], [s for s in P if s['type'] == 7]):
            if is_fx(x['data']) and x['size'] == p['size'] and x['data'] not in seen:
                seen.add(x['data']); out.append((n, x['data'], x['reloc'], p['data']))
    return out

CL = ('s32', 's16', 'raw', 'b2s16', 's16b2')
def conv(w, c):
    return {'s32': w[::-1], 's16': w[1::-1] + w[3:1:-1], 'raw': w, 'b2s16': w[0:2] + w[3:1:-1], 's16b2': w[1::-1] + w[2:4]}[c]
def compat(x, p): return frozenset(c for c in CL if conv(x, c) == p)

def idlists(d, t, end):
    """regione a liste {u32 n, n x u32}: ritorna [(offset, 'n'|'v')] o None se non torna esattamente"""
    o, out = t, []
    while o + 4 <= end:
        n = struct.unpack_from('>I', d, o)[0]
        if n > 64: return None
        out.append((o, 'n')); o += 4
        for k in range(n): out.append((o, 'v')); o += 4
    return out if o == end else None

def learn(S):
    tab = collections.defaultdict(collections.Counter)
    for n, xd, xr, pd in S:
        L = labels(xd, xr)
        if L is None: continue
        lab, ptr, ids = L
        for o, k in lab.items():
            if o in ptr or o in ids: continue
            tab[k][compat(xd[o:o + 4], pd[o:o + 4])] += 1
    return tab

def decide(cnt, need=1.0):
    """classe compatibile con (almeno need di) tutti i campioni; preferenza s32 > s16 > raw > misti"""
    tot = sum(cnt.values())
    if not tot: return None
    for c in CL:
        if sum(v for k, v in cnt.items() if c in k) >= need * tot: return c
    return None

if __name__ == '__main__':
    S = samples(); print('campioni', len(S), 'con struttura riconosciuta', sum(labels(x, r) is not None for _, x, r, _ in S))
    tab = learn(S)
    amb = {k: v for k, v in tab.items() if decide(v) is None}
    print('etichette', len(tab), 'ambigue', len(amb))
    for k, v in list(amb.items())[:12]: print('   ', k, dict(v))
    # leave-one-out
    ok = tot = unk = 0; bad = []; wrong = []
    for i, (n, xd, xr, pd) in enumerate(S):
        L = labels(xd, xr)
        if L is None: continue
        t2 = learn(S[:i] + S[i + 1:]); lab, ptr, ids = L
        for o, k in lab.items():
            if o in ptr or o in ids: continue
            if k[0] == 'reg' and k[1] == ('hdr', 8): continue          # liste: validate a parte
            c = decide(t2.get(k, {}))
            tot += 1
            if c is None or k not in t2: unk += 1; bad.append((n, hex(o), k, dict(t2.get(k, {})))) if len(bad) < 0 else None
            elif conv(xd[o:o + 4], c) == pd[o:o + 4]: ok += 1
            else: wrong.append((n.split('\\')[-1], hex(o), k, c, xd[o:o + 4].hex(), pd[o:o + 4].hex()))
    print('leave-one-out: parole', tot, 'giuste', ok, 'ignote', unk, 'SBAGLIATE', len(wrong))
    for w in wrong[:15]: print('   ', w)
    # liste {n, valori}: n e valori s32, valori piccoli = id texture (mappa tipo 5)
    import json
    tm = {int(a): b for a, b in json.load(open(os.path.join(W, 'generic', 'idmap.json')))['5'].items()}
    lt = lw = 0
    for n, xd, xr, pd in S:
        L = labels(xd, xr)
        if L is None: continue
        lab, ptr, ids = L
        offs = sorted(o for o, k in lab.items() if k[0] == 'reg' and k[1] == ('hdr', 8))
        if not offs: continue
        il = idlists(xd, offs[0], offs[-1] + 4)
        if il is None: print('   liste non parse', n); continue
        for o, kind in il:
            v = struct.unpack_from('>I', xd, o)[0]
            want = struct.unpack_from('<I', pd, o)[0]
            got = tm.get(v, v) if kind == 'v' and 0 < v < 0x10000 else v
            lt += 1; lw += got != want
            if got != want and lw < 6: print('   lista diff', n, hex(o), kind, hex(v), hex(got), hex(want))
    print('liste: parole', lt, 'sbagliate', lw)
