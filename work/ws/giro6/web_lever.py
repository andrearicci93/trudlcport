"""Giro 7 punto 2 (dopo il fix nebbia): per ogni ragnatela trova il valore della leva (c104.x oppure c100.w) per cui media(RGB*alfa) PC sui pixel-maglia = Xbox.
Scenari: (amb, ld) in (1,2) (1,0) (0.3,2), varianti Xbox 0/1 con lo slot PC corrispondente."""
import sys
sys.argv = [sys.argv[0]]
src = open('/path/to/trudlcport/work/ws/giro6/web_calib.py').read().replace('\nmain()\n', '\n')
exec(compile(src, 'web_calib', 'exec'))
OFFS = {'c104x': (4, 0), 'c100w': (0, 3)}
def pc_mean(prog, PPm, prow, amb, ld, lever, v):
    P = [p.copy() for p in PPm]
    if lever: P[OFFS[lever][0]][OFFS[lever][1]] = v
    e = env_for(11, P, amb, ld); c, m, k = runp(prog, e, prow, F9.ALLB, {15})
    mm = (m > .25) & ~(np.zeros(len(m), bool) if k is None else k); a = c[:, :3] * np.clip(c[:, 3:4], 0, 1)
    return a[mm].mean(), mm.sum()
res = {}
for mid in WEBS:
    rel, secs = find(mid); s = secs[(10, mid)]
    pe = C.entries(s.data, s.reloc, 'le'); xe = C.entries(*DM[mid], 'be')
    xl = struct.unpack_from('>4I', DM[mid][0], 0x28); pl = struct.unpack_from('<4I', s.data, 0x28)
    xrows = {e['slot']: (e['tex'], True) for e in xe}; prow = {e['slot']: (e['tex'], False) for e in pe}; STRAND[0] = prow[3][0]
    XPm = F10.params(F10.f9_common._Sec(*DM[mid]), 'be'); PPm = [np.array(v, np.float32) for v in F10.params(s, 'le')]
    fn = C.frame_lib(secs[(9, pl[2])].data)
    for var in (0, 1):
        pprog = sm3asm.decode(fn['entries'][fn['slots'][var]]['bc'])
        xblob = D[xl[2]]['entries'][D[xl[2]]['slots'][var]]['blob']; Kc = F9.Consts([])
        px = F9.translate_x(xblob, Kc.fn, lambda n, c: c, F9.xbools(xblob), opts=dict(B.material_opts(mid)))[0]
        xatt = {c['reg'] for c in XL.parse(xblob).ctab if c['set'] == 3 and 'Attenuation' in c['name']}
        for amb, ld in ((1.0, 2.0), (1.0, 0.0), (0.3, 2.0)):
            ex = env_for(11, XPm, amb, ld, Kc, True); cx, mx, kx = runp(px, ex, xrows, None, xatt)
            # maschera dal lato PC (stessa del calib)
            ep = env_for(11, PPm, amb, ld); cp, mp, kp = runp(pprog, ep, prow, F9.ALLB, {15}); mm = (mp > .25) & ~(np.zeros(len(mp), bool) if kx is None else kx)
            X = (cx[:, :3] * np.clip(cx[:, 3:4], 0, 1))[mm].mean()
            row = {}
            for lever in ('c104x', 'c100w'):
                p1, _ = pc_mean(pprog, PPm, prow, amb, ld, lever, 1.0); p0, _ = pc_mean(pprog, PPm, prow, amb, ld, lever, 0.5)
                pz, _ = pc_mean(pprog, PPm, prow, amb, ld, lever, 0.0)
                # secante tra 0 e 1 se (quasi) lineare; verifica nel punto trovato
                if p1 - pz < 1e-9: row[lever] = None; continue
                v = (X - pz) / (p1 - pz); chk, _ = pc_mean(pprog, PPm, prow, amb, ld, lever, v)
                row[lever] = (round(float(v), 3), round(float(chk / X), 3) if X > 1e-9 else None)
            res[(mid, var, amb, ld)] = (X, row)
            print('mat %d var%d amb %.1f ld %.1f  X=%.4f PC(K=1)=%.4f  leva (valore, PC/X verificato): %s' % (mid, var, amb, ld, X, p1 if False else pc_mean(pprog, PPm, prow, amb, ld, None, 0)[0], row), flush=True)
