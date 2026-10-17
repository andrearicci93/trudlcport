"""Risoluzione STRUTTURALE dei pareggi MaterialParams (giro 3, task 1). Regole, in ordine, per ogni lane PC in pareggio:
  S0  la lane PC non raggiunge le uscite del blocco luci (AST simbolico, sym_ast): irrilevante -> costante = valore del ponte
  S1  RAGGIUNGIBILITA': candidati ristretti alle lane Xbox che raggiungono le uscite del blocco Xbox (validata: 75/79 lane risolte per valore la rispettano;
      le 4 eccezioni sono lane solo-PC scelte per accordo statistico); se ne resta uno -> assegnato
  S2  FIRMA DI CONTESTO: espressione normalizzata dei consumatori (profondita' 1 sopra, 2 sotto, foglie astratte) uguale/piu' simile: candidato unico con punteggio > 0
      -> assegnato (validata: a livello (1,2) nessun disaccordo con le lane risolte per valore)
  S3  la lane PC raggiunge le uscite ma nessun candidato (non gia' usato) le raggiunge: lane solo-PC -> costante = valore del ponte
Iniettivita': una lane Xbox gia' assegnata a un'altra lane PC non e' candidata (tranne S3).
Ritorna (res aggiornato, pareggi residui, note)."""
import sys; sys.path.insert(0, '/path/to/trudlcport/work/ws/codefirst')
from xp_struct import *

def apply(xs, pd, res, ties):
    if not ties: return res, ties, {}
    C, _r, _t, out, _x, _p = struct_scores(xs, pd)
    CP2, CX2 = out[(1, 2)]; CP1, CX1 = out[(1, 1)]
    PP = C['PP']
    new = dict(res); notes = {}; left = {}
    used = {tuple(v) for (k, v) in res.values() if k == 'lane'}
    L = lambda l: 'c%d.%s' % (l[0], 'xyzw'[l[1]])
    for l in sorted(ties, key=lambda t: (len(ties[t]), t)):
        cands = [tuple(x) for x in ties[l]]
        bridge_val = float(PP[l[0] - 100][l[1]])
        if l not in CP2 and l not in CP1:
            new[l] = ('const', bridge_val); notes[l] = 'S0 lane PC non raggiunge le uscite -> costante %g' % bridge_val; continue
        live = [x for x in cands if x in CX2 and x not in used]
        if len(live) == 1:
            new[l] = ('lane', live[0]); used.add(live[0]); notes[l] = 'S1 unico candidato che raggiunge le uscite Xbox: %s' % L(live[0]); continue
        if not live:
            new[l] = ('const', bridge_val); notes[l] = 'S3 lane solo-PC (nessun candidato raggiunge le uscite Xbox) -> costante %g' % bridge_val; continue
        b, sc = best(out, l, live)
        if b and len(b[0]) == 1 and b[1] > 0 and b[2] == (1, 2):
            new[l] = ('lane', b[0][0]); used.add(b[0][0]); notes[l] = 'S2 firma di contesto (%s, punteggio %.2f su candidati %s)' % (L(b[0][0]), b[1], {L(x): round(v, 2) for x, v in sc.items()}); continue
        # nessuna regola decide: S3 se nessun candidato ha alcuna somiglianza strutturale
        if all(v == 0 for v in sc.values()):
            new[l] = ('const', bridge_val); notes[l] = 'S3 nessun candidato strutturalmente simile -> lane solo-PC, costante %g' % bridge_val; continue
        left[l] = ties[l]; notes[l] = 'IRRISOLTO %s' % {L(x): round(v, 2) for x, v in sc.items()}
    return new, left, notes

if __name__ == '__main__':
    import mp_resolve
    for xs, pd in zip(map(int, sys.argv[1::2]), map(int, sys.argv[2::2])):
        res, ties = mp_resolve.resolve(xs, pd)
        new, left, notes = apply(xs, pd, res, ties)
        print('=== (%d,%d): pareggi %d -> residui %d' % (xs, pd, len(ties), len(left)))
        for l, n in sorted(notes.items()): print('  c%d.%s: %s  => %s' % (l[0], 'xyzw'[l[1]], n, new.get(l)))
