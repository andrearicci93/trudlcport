import sys; sys.path.insert(0, '/path/to/trudlcport/work/ws/codefirst')
from xp_func import *
xs, pd = int(sys.argv[1]), int(sys.argv[2])
C, res, ties = get_ctx(xs, pd)
print('p_to_s_out', C['p_to_s_out']); print('p_from_s', C['p_from_s']); print('p_const', C['p_const'])
XP, PP = C['XP'], C['PP']
rows_x = {100 + j: XP[j] for j in range(len(XP))}; rows_p = {100 + j: PP[j] for j in range(len(PP))}
rx = block_run(C, 'x', rows_x, 0); rp = block_run(C, 'p', rows_p, 0)
print('reale per uscita', ['%.3f' % a for a in outs_agree(C, rx, rp)])
# stessi valori ma sostituendo con la regola
v = {(100 + j, c): float(XP[j][c]) for j in range(len(XP)) for c in range(4)}
rp2 = block_run(C, 'p', pc_rows(C, res, {l: ties[l][0] for l in ties}, v), 0)
print('regola su valori reali', ['%.3f' % a for a in outs_agree(C, rx, rp2)])
