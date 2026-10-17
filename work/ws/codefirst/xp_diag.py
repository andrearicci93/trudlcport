import sys; sys.path.insert(0, '/path/to/trudlcport/work/ws/codefirst')
import numpy as np
from mp_cands import *
from f9_transplant import *
import bridge_ext
xs, pd = int(sys.argv[1]), int(sys.argv[2])
env = Env(2)
pA, a0, a1, inA, outA = xblock_info('X', xs, 0); pB, b0, b1, inB, outB = bridge_ext.pc_block_info(pd, 0)
fA, bA = fingerprints(pA, a0, a1, inA, outA, env, ALLB); fB, bB = fingerprints(pB, b0, b1, inB, outB, env, ALLB)
print('outA', outA); print('outB', outB); print('inA', inA); print('inB', inB)
for ob in outB:
    m = [oa for oa in outA if np.allclose(bA[oa], bB[ob], **TOL)]
    print('uscita PC', ob, '<- candidati base uguali:', m)
