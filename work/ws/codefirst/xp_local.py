"""Espressioni locali normalizzate (consumatori di profondita' 2) di ogni lane MP, foglie astratte: lane marcata 'L', altre MP -> nome lane, input -> in, k -> k.
Uso: xp_local.py XS PD"""
import sys; sys.path.insert(0, '/path/to/trudlcport/work/ws/codefirst')
from xp_roles import *

def abstract(D, n, target, depth, names):
    t = D.nodes[n]
    if t[0] == 'L':
        if t[1] == 'mp': return 'L' if (t[2], t[3]) == target else names(t[2], t[3])
        if t[1] == 'lit': return '%g' % t[2]
        return t[1]
    if depth == 0: return '_'
    sub = [abstract(D, c, target, depth - 1, names) for c in t[1:]]
    if t[0] in ('add', 'mul'): sub = sorted(sub)
    return '%s(%s)' % (t[0], ','.join(sub))

def contexts(D, roots, names, depth_up=2, depth_down=2):
    parents = collections.defaultdict(set); seen = set(); st = list(roots)
    while st:
        n = st.pop()
        if n in seen: continue
        seen.add(n); t = D.nodes[n]
        if t[0] == 'L': continue
        for c in t[1:]: parents[c].add(n); st.append(c)
    res = collections.defaultdict(collections.Counter)
    for n in seen:
        t = D.nodes[n]
        if t[0] == 'L' and t[1] == 'mp':
            lane = (t[2], t[3])
            # sale di depth_up livelli lungo i genitori; stampa l'espressione astratta del nodo raggiunto
            fr = {n}
            for _ in range(depth_up):
                fr = {p for x in fr for p in parents.get(x, ())} or fr
            for p in fr: res[lane][abstract(D, p, lane, depth_down + depth_up, names)] += 1
    return res

def main():
    xs, pd = int(sys.argv[1]), int(sys.argv[2]); up = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    C, res, ties, (DX, ex, lx, RX), (DP, ep, lp, RP) = analyse(xs, pd, 3)
    rx = [ex[o] for o in C['sout'] if o in ex]; rpp = [ep[o] for o in C['pout'] if o in ep]
    nm = lambda r, c: 'M'  # sibling MP astratta: il ruolo e' dato dalla struttura, non dal nome del registro
    CX = contexts(DX, rx, nm, up, 2); CP = contexts(DP, rpp, nm, up, 2)
    L = lambda l: 'c%d.%s' % (l[0], 'xyzw'[l[1]])
    for title, CC, D in (('PC', CP, DP), ('XBOX', CX, DX)):
        print('\n########', title)
        for l in sorted(CC):
            print(' ', L(l))
            for e, n in CC[l].most_common(4): print('      x%-3d %s' % (n, e[:260]))
if __name__ == '__main__': main()
