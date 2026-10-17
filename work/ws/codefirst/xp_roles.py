"""Confronto delle firme di ruolo (sym_ast.roles) fra lane PC e lane Xbox del blocco luci, famiglia (xs,pd). Uso: xp_roles.py XS PD [profondita']"""
import sys; sys.path.insert(0, '/path/to/trudlcport/work/ws/codefirst')
from xp_func import *
import sym_ast as SA

def analyse(xs, pd, depth=3):
    C, res, ties = get_ctx(xs, pd)
    DX, ex, lx = SA.build(C['sprog'], C['s0'], C['s1']); DP, ep, lp = SA.build(C['pprog'], C['p0'], C['p1'])
    rx = [ex[o] for o in C['sout'] if o in ex]; rpp = [ep[o] for o in C['pout'] if o in ep]
    RX = SA.roles(DX, rx, depth); RP = SA.roles(DP, rpp, depth)
    return C, res, ties, (DX, ex, lx, RX), (DP, ep, lp, RP)

def jac(a, b):
    return len(a & b) / max(1, len(a | b))

def main():
    xs, pd = int(sys.argv[1]), int(sys.argv[2]); depth = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    C, res, ties, (DX, ex, lx, RX), (DP, ep, lp, RP) = analyse(xs, pd, depth)
    L = lambda l: 'c%d.%s' % (l[0], 'xyzw'[l[1]])
    print('=== (%d,%d) profondita %d; lane PC con firma %d, lane Xbox con firma %d' % (xs, pd, depth, len(RP), len(RX)))
    for l in sorted(RP):
        sc = sorted(((jac(RP[l], RX[x]), x) for x in RX), reverse=True)
        known = res.get(l)
        kn = ('c%d.%s' % (known[1][0], 'xyzw'[known[1][1]])) if known and known[0] == 'lane' else (str(known[0]) if known else '-')
        print(' PC %s (regola %s, %s): firme %d | migliori Xbox: %s' % (L(l), kn, [L(t) for t in ties.get(l, [])] if l in ties else '', len(RP[l]), ', '.join('%s=%.2f' % (L(x), j) for j, x in sc[:5])))
if __name__ == '__main__': main()
