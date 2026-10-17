"""Task 1 (giro 3): matching FUNZIONALE cross-piattaforma del blocco luci Xbox (xs) vs PC (pd): firme di sensibilita' (derivate numeriche
dell'uscita rispetto a ogni lane d'ingresso, su ingressi casuali) -- nessun valore di materiale. Uso: xp_match.py XS PD"""
import sys; sys.path.insert(0, '/path/to/trudlcport/work/ws/codefirst')
import numpy as np
from match_all import *
import match_all as MA
from mp_cands import *
import bridge_ext
from f9_transplant import *

def main(xs, pd, cap=50):
    env = Env(2)
    A = xblock_info('X', xs, 0); B = bridge_ext.pc_block_info(pd, 0)
    pA, a0, a1, inA, outA = A; pB, b0, b1, inB, outB = B
    print('Xs: in %d out %d ; Pd: in %d out %d' % (len(inA), len(outA), len(inB), len(outB)))
    sol = MA.match_all(pA, a0, a1, inA, outA, pB, b0, b1, inB, outB, env, cap=cap, bools=ALLB)
    print('soluzioni:', len(sol))
    for im, om in sol[:cap]:
        mp = {k: v for k, v in im.items() if len(k) == 3}
        print(' MP:', {('c%d.%s' % (k[1], 'xyzw'[k[2]])): ('c%d.%s' % (v[1], 'xyzw'[v[2]])) for k, v in sorted(mp.items())})
    return sol
if __name__ == '__main__': main(int(sys.argv[1]), int(sys.argv[2]))
