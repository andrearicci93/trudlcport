"""Debug helper: locate the smallest sub-expression where D and S fail to unify.  usage: explain.py DLIB SLIB [slot] [rootcomp]"""
import sys, os, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import xenos_xlat as X, xenos_map as M

def dry(U, a, b):
    return U.uni(a, b, collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter), 2, False)

_DESC = {}
def desc(sh, ir, n):
    k = (id(ir), n)
    if k in _DESC: return _DESC[k]
    nd = ir.nodes[n]; r = {sh.of(n)}
    for c in nd[1:]:
        if isinstance(c, int) and not isinstance(c, bool) and nd[0] not in ('P', 'C', 'V', 'U', 'k'): r |= desc(sh, ir, c)
    _DESC[k] = r
    return r

def explain(U, a, b, depth=0, out=None, maxdepth=60):
    nd, ns = U.D.nodes[a], U.S.nodes[b]
    if nd[0] != ns[0]:
        return [('KIND', X.ir_str(U.D, a, 0, 3)[:160], X.ir_str(U.S, b, 0, 3)[:160])]
    if nd[0] in ('add', 'mul', 'max', 'min', 'seq', 'sne'):
        ga = collections.defaultdict(list); gb = collections.defaultdict(list)
        for c in nd[1:]: ga[U.shD.of(c)].append(c)
        for c in ns[1:]: gb[U.shS.of(c)].append(c)
        if {k: len(v) for k, v in ga.items()} != {k: len(v) for k, v in gb.items()}:
            onlyD = [c for k in ga for c in ga[k][len(gb.get(k, [])):]]
            onlyS = [c for k in gb for c in gb[k][len(ga.get(k, [])):]]
            # recurse into the most similar unmatched pair (by shared descendant shapes), if any
            if onlyD and onlyS and depth < 40:
                best = max(((len(desc(U.shD, U.D, c) & desc(U.shS, U.S, d)), c, d) for c in onlyD for d in onlyS), key=lambda t: t[0])
                if best[0] > 0 and U.D.nodes[best[1]][0] == U.S.nodes[best[2]][0] and (best[1], best[2]) != (a, b):
                    return explain(U, best[1], best[2], depth + 1)
            return [('NARY ' + nd[0], 'only D: ' + ' | '.join(X.ir_str(U.D, c, 0, 3)[:90] for c in onlyD[:3]), 'only S: ' + ' | '.join(X.ir_str(U.S, c, 0, 3)[:90] for c in onlyS[:3]))]
        for k in ga:
            if len(ga[k]) == 1 and not dry(U, ga[k][0], gb[k][0]):
                return explain(U, ga[k][0], gb[k][0], depth + 1)
        return [('NARY-ambiguous', nd[0], '')]
    if depth > maxdepth: return [('deep', '', '')]
    for c1, c2 in zip(nd[1:], ns[1:]):
        if isinstance(c1, int) and isinstance(c2, int) and not isinstance(c1, bool) and not dry(U, c1, c2):
            return explain(U, c1, c2, depth + 1)
    return [('LEAF', str(nd)[:100], str(ns)[:100])]

if __name__ == '__main__':
    L = X.load_libs(); D, Xl = L['D'], L['X']
    dl, sl = int(sys.argv[1]), int(sys.argv[2]); slot = int(sys.argv[3]) if len(sys.argv) > 3 else None
    for si, (sa, sb) in enumerate(zip(D[dl]['slots'], Xl[sl]['slots'])):
        if sa == 0xffffffff or sb == 0xffffffff or (slot is not None and si != slot): continue
        shD, bD, rD = M.build_ir(D[dl]['entries'][sa]['blob']); shS, bS, rS = M.build_ir(Xl[sl]['entries'][sb]['blob'])
        U = M.Unifier(bD.ir, bS.ir); U.established = {}
        print('slot', si, 'roots', len(rD), len(rS))
        for k in sorted(set(rD) & set(rS))[:int(sys.argv[4]) if len(sys.argv) > 4 else 2]:
            ok = dry(U, rD[k], rS[k])
            print(' root', k, 'ok' if ok else 'FAIL')
            if not ok:
                for e in explain(U, rD[k], rS[k]): print('   ', e)
