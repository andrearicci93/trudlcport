"""Regola STRUTTURALE per le lane MaterialParams: per ogni lane PC, le lane Xbox con la stessa firma di contesto locale (espressione normalizzata dei consumatori,
foglie astratte, solo lane che raggiungono le uscite del blocco). Validata sulle lane gia' risolte per valore (stesse famiglie), poi applicata ai pareggi.
Uso: xp_struct.py XS PD [XS PD ...]"""
import sys; sys.path.insert(0, '/path/to/trudlcport/work/ws/codefirst')
from xp_local import *

def jacc(a, b):
    ka = set(a) | set(b)
    return sum(min(a[k], b[k]) / max(a[k], b[k]) for k in ka if k in a and k in b) / max(1, len(ka)) if ka else 0.0

def struct_scores(xs, pd):
    C, res, ties, (DX, ex, lx, RX), (DP, ep, lp, RP) = analyse(xs, pd, 3)
    rx = [ex[o] for o in C['sout'] if o in ex]; rpp = [ep[o] for o in C['pout'] if o in ep]
    nm = lambda r, c: 'M'
    out = {}
    for ud, dd in ((1, 2), (1, 1)):
        CX = contexts(DX, rx, nm, ud, dd); CP = contexts(DP, rpp, nm, ud, dd)
        out[(ud, dd)] = (CP, CX)
    return C, res, ties, out, (DX, ex), (DP, ep)

TIERS = ((1, 2), (1, 1))

def best(out, l, cands=None):
    """primo livello di dettaglio (espressione profonda, poi solo operatori) in cui il migliore ha punteggio > 0; ritorna ((top, punteggio, livello), punteggi)."""
    for t in TIERS:
        CP, CX = out[t]
        if l not in CP: return None, {}
        sc = {x: jacc(CP[l], CX[x]) for x in (cands or CX) if x in CX}
        if not sc: return None, {}
        m = max(sc.values())
        if m > 0:
            top = [x for x, v in sc.items() if v >= m - 1e-9]
            return (top, m, t), sc
    return None, sc

def main():
    a = sys.argv[1:]
    L = lambda l: 'c%d.%s' % (l[0], 'xyzw'[l[1]])
    for xs, pd in zip(map(int, a[0::2]), map(int, a[1::2])):
        C, res, ties, out, _, _ = struct_scores(xs, pd)
        CP, CX = out[(1, 2)]
        print('=== (%d,%d)' % (xs, pd))
        agree = dis = 0
        for l, (kind, val) in sorted(res.items()):
            if l not in CP: print('  PC %s: %s %s -> morta (non raggiunge le uscite)' % (L(l), kind, val if kind != 'lane' else L(val))); continue
            if kind == 'lane':
                b, sc = best(out, l)
                ok = b is not None and tuple(val) in b[0]
                u = len(b[0]) == 1 if b else False
                agree += ok; dis += (not ok)
                print('  PC %s <- valore %s | struttura %s (%.2f, liv %s)%s %s' % (L(l), L(val), [L(x) for x in b[0]][:4] if b else None, b[1] if b else 0, b[2] if b else '-', ' UNICA' if u else '', 'OK' if ok else 'DISACCORDO'))
            elif kind == 'tie':
                cands = [tuple(x) for x in ties[l]]
                b, sc = best(out, l, cands)
                print('  PC %s PAREGGIO %s -> struttura %s %s' % (L(l), [L(x) for x in cands], {L(x): round(v, 2) for x, v in sc.items()}, ('=> ' + L(b[0][0])) if b and len(b[0]) == 1 and b[1] > 0 else '=> AMBIGUO'))
            else: print('  PC %s: %s %s' % (L(l), kind, val))
        print('  accordo struttura/valore: %d ok, %d disaccordi' % (agree, dis), flush=True)
if __name__ == '__main__': main()
