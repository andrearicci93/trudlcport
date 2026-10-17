import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from f3_validate import *
x, p, xs = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
L = libs(); X, P = L['X'], L['P']
blob = X[x]['entries'][X[x]['slots'][xs]]['blob']
sh = XL.parse(blob)
print('\n'.join(XL.text(sh, 'pretty').lines)); print('interp', sh.interp, 'svpos', sh.svpos_reg)
tr = xenos2sm3.translate(blob, const_fn)
print('=== translated'); print(tr.text)
ks = [k for k in range(8) if (k & 1) == xs and P[p]['slots'][k] != 0xffffffff]
pb = P[p]['entries'][P[p]['slots'][ks[0]]]['blob']
print('=== PC twin slot', ks[0]); print(sm3dis.disassemble(pb[:sm3dis.bytecode_len(pb)], False))
