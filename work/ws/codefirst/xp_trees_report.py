"""Task 1 (Giro 3): alberi di espressione (dataflow slice) dal punto di lettura della lane MaterialParams all'uscita del blocco luci.
Per ogni lane: numero di consumatori diretti, cammino piu' breve foglia->uscita (op, ruolo del figlio: base/esponente/termine, fratelli abbreviati),
firma di contesto normalizzata (livello 1,2) e quali uscite raggiunge. Uso: xp_trees_report.py 1431 1060"""
import sys; sys.path.insert(0, '/path/to/trudlcport/work/ws/codefirst')
from xp_local import *
import collections

def run(xs, pd):
    C, res, ties, (DX, ex, lx, RX), (DP, ep, lp, RP) = analyse(xs, pd, 3)
    rx = {o: ex[o] for o in C['sout'] if o in ex}; rp = {o: ep[o] for o in C['pout'] if o in ep}
    L = lambda l: 'c%d.%s' % (l[0], 'xyzw'[l[1]])
    def parents_of(D, roots):
        par = collections.defaultdict(set); seen = set(); st = list(roots)
        while st:
            n = st.pop()
            if n in seen: continue
            seen.add(n); t = D.nodes[n]
            if t[0] == 'L': continue
            for pos, c in enumerate(t[1:]): par[c].add((n, pos)); st.append(c)
        return par, seen
    def lane_leaf(D, seen, lane):
        for n in seen:
            t = D.nodes[n]
            if t[0] == 'L' and t[1] == 'mp' and (t[2], t[3]) == lane: return n
    def role(D, p, pos):
        t = D.nodes[p]
        if t[0] == 'pow': return ('base', 'ESPONENTE')[pos]
        if t[0] in ('add', 'mul'): return 'termine'
        return 'arg%d' % pos
    def sib(D, p, child, lane):
        t = D.nodes[p]; out = []
        for c in t[1:]:
            if c == child: continue
            out.append(SA.show(D, c, 2))
        return ', '.join(out)[:150]
    def path(D, par, roots_by_node, leaf):
        # BFS verso l'alto fino a un nodo-uscita
        q = collections.deque([(leaf, [])]); seen = {leaf}
        while q:
            n, pth = q.popleft()
            if n in roots_by_node: return pth, roots_by_node[n]
            for (p, pos) in sorted(par.get(n, ())):
                if p not in seen: seen.add(p); q.append((p, pth + [(p, pos, n)]))
        return None, None
    def reach(D, par, roots_by_node, leaf):
        seen = {leaf}; st = [leaf]; hit = set()
        while st:
            n = st.pop()
            if n in roots_by_node: hit.add(roots_by_node[n])
            for (p, pos) in par.get(n, ()):
                if p not in seen: seen.add(p); st.append(p)
        return sorted(hit)
    def report(title, D, roots, lanes, CTX):
        par, seen = parents_of(D, roots.values()); rbn = {n: o for o, n in roots.items()}
        print('\n######## %s' % title)
        for lane in lanes:
            lf = lane_leaf(D, seen, lane)
            if lf is None: print('\n  %s: NON RAGGIUNGE LE USCITE del blocco luci (nessun consumatore nella slice)' % L(lane)); continue
            ps = sorted(par.get(lf, ()))
            print('\n  %s: %d consumatori diretti; raggiunge %d uscite %s' % (L(lane), len(ps), len(reach(D, par, rbn, lf)), reach(D, par, rbn, lf)[:6]))
            pth, o = path(D, par, rbn, lf)
            for (p, pos, ch) in (pth or [])[:6]:
                t = D.nodes[p]
                print('      %-5s [%s] <- %s' % (t[0], role(D, p, pos), 'lane' ), '| altri operandi:', sib(D, p, ch, lane))
            print('      -> uscita', o)
            print('      firme di contesto (L = la lane):')
            for e, n in CTX.get(lane, collections.Counter()).most_common(3): print('         x%-3d %s' % (n, e[:200]))
    nm = lambda r, c: 'M'
    CX = contexts(DX, list(rx.values()), nm, 1, 2); CP = contexts(DP, list(rp.values()), nm, 1, 2)
    report('PC Pd=%d (lane in pareggio + riferimenti gia\' decisi)' % pd, DP, rp, [(107, 1), (108, 0), (108, 2), (109, 0), (109, 3), (103, 0), (101, 0), (108, 3)], CP)
    report('XBOX Xs=%d (candidati e scartati)' % xs, DX, rx, [(109, 0), (109, 1), (107, 0), (107, 1), (107, 2), (107, 3), (100, 3), (102, 0), (100, 0), (108, 0)], CX)

if __name__ == '__main__':
    run(int(sys.argv[1]), int(sys.argv[2]))
