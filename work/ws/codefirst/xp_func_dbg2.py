import sys; sys.path.insert(0, '/path/to/trudlcport/work/ws/codefirst')
from xp_func import *
xs, pd = int(sys.argv[1]), int(sys.argv[2])
C, res, ties = get_ctx(xs, pd)
XP, PP = C['XP'], C['PP']
def run(which, rows, bl):
    env = C['envx'] if which == 'x' else C['envp']; consts = dict(env.consts)
    for r, v in rows.items(): consts[r] = np.array(v, np.float32)
    if which == 'x': st, prog, a, b = C['sts'], C['sprog'], C['s0'], C['s1']
    else: st, prog, a, b = C['stp'], C['pprog'], C['p0'], C['p1']
    return run_state(prog, body(prog)[a:b], st, consts, env.tex, env.N, bl)[0]
rows_x = {100 + j: XP[j] for j in range(len(XP))}; rows_p = {100 + j: PP[j] for j in range(len(PP))}
print('bool Xs: ', end=''); 
for lab, blx in (('None', None), ('ALLB', ALLB), ('{}', {})):
    for labp, blp in (('ALLB', ALLB), ('{}', {})):
        rx = run('x', rows_x, blx); rp = run('p', rows_p, blp)
        print(' Xs=%s Pd=%s: %s' % (lab, labp, ['%.2f' % a for a in outs_agree(C, rx, rp)]))
