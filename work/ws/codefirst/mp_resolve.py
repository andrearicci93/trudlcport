"""Risolutore MaterialParams per famiglia (xs, pd): per ogni lane PC letta dal blocco luci di pd -> lane Xbox (spazio xs).
Regole, tutte da codice/dati (nessuna euristica a occhio):
  R1 candidati = lane Xbox compatibili per valore con TUTTI i campioni (ponte reale + ponti estesi di coppie con blocchi luci Xbox E PC
     equivalenti, luci accese lato PC), tenendo conto delle simmetrie dei blocchi (mp_cands.py)
  R2 nessun candidato e valore PC costante in tutti i campioni -> costante (def)
  R3 pareggi: (a) i vec3 colore si muovono come unita' (se le lane sorelle x/z della stessa riga PC puntano alla riga Xbox R, la lane y vale R.y);
             (b) iniettivita' (una lane Xbox alimenta una sola lane PC se esiste una assegnazione iniettiva); (c) i pareggi residui sono
             riportati in 'ties' e vanno verificati per materiale (innocui se i valori Xbox dei candidati coincidono nel materiale)
Ritorna dict lane -> ('lane',(r,c)) | ('const',v) | ('tie',[cands])  + ties dict."""
import sys, itertools
sys.path.insert(0, '/path/to/trudlcport/work/ws/codefirst')
from mp_cands import *

_RES = {}
EXC = {}
AGR = {}
import collections


def resolve(xs, pd, slot=0):
    key = (xs, pd, slot)
    if key in _RES: return _RES[key]
    PA = bridge_ext.pc_block_info(pd, slot); A = xblock_info('X', xs, slot)
    mpd = sorted((k[1], k[2]) for k in PA[3] if len(k) == 3); ms = sorted((k[1], k[2]) for k in A[3] if len(k) == 3)
    M = members(xs, pd, slot)
    cand = {}
    for l in mpd:
        cs = []
        for x in ms:
            ok = True
            for s in M:
                Ls = inv_alt(s['pmap'], s['pcls'], l); Xs_ = inv_alt(s['xmap'], s['xcls'], x)
                if not any((val(s['PP'], a) is not None and val(s['XP'], b) is not None and abs(val(s['PP'], a) - val(s['XP'], b)) < 1e-6) for a in Ls for b in Xs_):
                    ok = False; break
            if ok: cs.append(x)
        cand[l] = cs
    res = {}; exc = {}
    for l in mpd:
        if cand[l]: continue
        vals = []
        for s_ in M:
            srcs = [k for k, v in (s_['pmap'] or {l: l}).items() if v == l]
            vv = val(s_['PP'], srcs[0]) if srcs else None
            if vv is not None: vals.append((round(float(vv), 6), s_['tag']))
        cnt = collections.Counter(v for v, _ in vals); mode, nmode = cnt.most_common(1)[0]
        if nmode >= 0.9 * len(vals): res[l] = ('const', mode); exc[l] = [(v, t) for v, t in vals if v != mode]
        else: res[l] = ('none', sorted(cnt))
    # R3a: colori come unita'
    rows = {}
    for l in mpd:
        if len(cand[l]) == 1: rows.setdefault(l[0], set()).add(cand[l][0][0])
    for l in mpd:
        if len(cand[l]) > 1:
            sib = [cand[(l[0], c)][0] for c in range(3) if c != l[1] and (l[0], c) in cand and len(cand[(l[0], c)]) == 1]
            if len(sib) >= 2 and len({s[0] for s in sib}) == 1:
                tgt = (sib[0][0], l[1])
                if tgt in cand[l]: cand[l] = [tgt]
    # R3b: iniettivita' fra le lane ancora in pareggio
    fixed = {cand[l][0] for l in mpd if len(cand[l]) == 1}
    for l in mpd:
        if len(cand[l]) > 1:
            rest = [x for x in cand[l] if x not in fixed]
            if len(rest) == 1: cand[l] = rest
    # R3c: accordo ESATTO (rappresentante di ogni membro, senza classi di simmetria) fra lane PC e ciascun candidato rimasto
    def exact(mp, lane):
        if mp is None: return lane
        k = [kk for kk, v in mp.items() if v == lane]; return k[0] if k else None
    def agree(l, x):
        n = tot = 0
        for s_ in M:
            a, b = exact(s_['pmap'], l), exact(s_['xmap'], x)
            va, vb = (val(s_['PP'], a) if a else None), (val(s_['XP'], b) if b else None)
            if va is None or vb is None: continue
            tot += 1; n += abs(va - vb) < 1e-6
        return n, tot
    AG = {}
    for l in mpd:
        if len(cand[l]) > 1 and l not in res:
            sc = {x: agree(l, x) for x in cand[l]}; AG[l] = sc
            best = max(sc.values(), key=lambda t: t[0] / max(t[1], 1)); bf = best[0] / max(best[1], 1)
            top = [x for x in cand[l] if sc[x][0] / max(sc[x][1], 1) >= bf - 1e-9]
            if best[1] >= 5 and bf >= 0.85 and len(top) == 1: cand[l] = top; continue
            # lane PC quasi costante e senza candidato che la copi: lane solo-PC
            vals = [round(float(val(s_['PP'], exact(s_['pmap'], l))), 6) for s_ in M if exact(s_['pmap'], l) is not None and val(s_['PP'], exact(s_['pmap'], l)) is not None]
            cnt = collections.Counter(vals); mode, nmode = cnt.most_common(1)[0]
            if len(vals) >= 5 and bf < 0.5 and nmode >= 0.85 * len(vals): res[l] = ('const', mode); exc[l] = [v for v in vals if v != mode]
    ties = {}
    for l in mpd:
        if l in res: continue
        if len(cand[l]) == 1: res[l] = ('lane', cand[l][0])
        else: res[l] = ('tie', cand[l]); ties[l] = cand[l]
    _RES[key] = (res, ties); EXC[key] = exc; AGR[key] = AG
    return res, ties


if __name__ == '__main__':
    xs, pd = int(sys.argv[1]), int(sys.argv[2])
    res, ties = resolve(xs, pd)
    for l, v in sorted(res.items()): print('PC c%d.%s -> %s' % (l[0], 'xyzw'[l[1]], v if v[0] != 'lane' else 'Xbox c%d.%s' % (v[1][0], 'xyzw'[v[1][1]])))
