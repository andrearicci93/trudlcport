import sys, io, contextlib
sys.argv = [sys.argv[0]]
src = open('/path/to/trudlcport/work/ws/giro6/web_calib.py').read().replace('\nmain()\n', '\n')
exec(compile(src, 'web_calib', 'exec'))
mid = 23173
rel, secs = find(mid); s = secs[(10, mid)]
pe = C.entries(s.data, s.reloc, 'le'); prow = {e['slot']: (e['tex'], False) for e in pe}
pl = struct.unpack_from('<4I', s.data, 0x28)
PPm = [np.array(v, np.float32) for v in F10.params(s, 'le')]
fn = C.frame_lib(secs[(9, pl[2])].data)
for slot in range(8):
    prog = sm3asm.decode(fn['entries'][fn['slots'][slot]]['bc'])
    reads = sorted({o.num for i in prog.instrs() for o in i.ops if o.rtype == sm3asm.RT_CONST and not o.isdst})
    def meas(env):
        c, m, k = runp(prog, env, prow, F9.ALLB, {15})
        a = c[:, :3] * np.clip(c[:, 3:4], 0, 1); mm = (m > .25) & ~(np.zeros(len(m), bool) if k is None else k)
        return a[mm].mean(), c[mm, 3].mean(), mm.sum()
    base = meas(env_for(11, PPm, 1.0, 2.0))
    out = []
    for r in reads:
        e = env_for(11, PPm, 1.0, 2.0); e.consts[r] = e.consts[r] * 0 + 3.0 if r not in (54,) else e.consts[r]
        v = meas(e)
        if abs(v[0] - base[0]) > 1e-4 or abs(v[1] - base[1]) > 1e-4: out.append((r, round(float(v[0]), 3), round(float(v[1]), 3)))
    print('slot', slot, 'base rgb*a/alfa/n', np.round(base[0], 3), np.round(base[1], 3), base[2], 'sensibile a (reg, rgb*a, alfa) con reg=3.0:', out)
