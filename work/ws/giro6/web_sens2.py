import sys
sys.argv = [sys.argv[0]]
src = open('/path/to/trudlcport/work/ws/giro6/web_calib.py').read().replace('\nmain()\n', '\n')
exec(compile(src, 'web_calib', 'exec'))
mid = 23173
rel, secs = find(mid); s = secs[(10, mid)]
pe = C.entries(s.data, s.reloc, 'le'); xe = C.entries(*DM[mid], 'be')
xrows = {e['slot']: (e['tex'], True) for e in xe}; STRAND[0] = 6610
xl = struct.unpack_from('>4I', DM[mid][0], 0x28)
XPm = F10.params(F10.f9_common._Sec(*DM[mid]), 'be')
for var in (0, 1):
    xblob = D[xl[2]]['entries'][D[xl[2]]['slots'][var]]['blob']
    Kc = F9.Consts([]); px = F9.translate_x(xblob, Kc.fn, lambda n, c: c, F9.xbools(xblob), opts=dict(B.material_opts(mid)))[0]
    xatt = {c['reg'] for c in XL.parse(xblob).ctab if c['set'] == 3 and 'Attenuation' in c['name']}
    nm = {c['name']: c['reg'] for c in XL.parse(xblob).ctab if c['set'] == 2}
    reads = sorted({o.num for i in px.instrs() for o in i.ops if o.rtype == sm3asm.RT_CONST and not o.isdst})
    inv = {}
    for n, (r, c) in Kc.pfl.items():
        for j in range(c): inv[r + j] = n
    for (n, j), r in Kc.extra.items(): inv[r] = 'extra:%s+%d' % (n, j)
    def meas(env):
        c, m, k = runp(px, env, xrows, None, xatt)
        mm = (m > .25) & ~(np.zeros(len(m), bool) if k is None else k); a = c[:, :3] * np.clip(c[:, 3:4], 0, 1)
        return a[mm].mean(), c[mm, 3].mean()
    base = meas(env_for(11, XPm, 1.0, 2.0, Kc, True)); out = []
    for r in reads:
        e = env_for(11, XPm, 1.0, 2.0, Kc, True); e.consts[r] = e.consts[r] * 0 + 3.0; v = meas(e)
        if abs(v[0] - base[0]) > 1e-4 or abs(v[1] - base[1]) > 1e-4: out.append((r, inv.get(r), round(float(v[0]), 3), round(float(v[1]), 3)))
    print('Xbox var', var, 'base', np.round(base, 3), 'sensibile:', out[:14], '... totale', len(out))
