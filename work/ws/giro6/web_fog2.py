import sys
sys.argv = [sys.argv[0]]
src = open('/path/to/trudlcport/work/ws/giro6/web_calib.py').read().replace('\nmain()\n', '\n')
exec(compile(src, 'web_calib', 'exec'))
mid = 23173
xl = struct.unpack_from('>4I', DM[mid][0], 0x28)
xblob = D[xl[2]]['entries'][D[xl[2]]['slots'][0]]['blob']
Kc = F9.Consts([]); px = F9.translate_x(xblob, Kc.fn, lambda n, c: c, F9.xbools(xblob), opts=dict(B.material_opts(mid)))[0]
ins = list(px.instrs()); print(len(ins)); 
inv = {r: k for k, r in Kc.extra.items()}
print({k: r for k, r in Kc.extra.items() if 'Fog' in k[0] or 'Height' in k[0]}, [ (n,(r,c)) for n,(r,c) in Kc.pfl.items() if 'Fog' in n])
for n in range(len(ins) - 14, len(ins)): print(n, sm3asm.fmt_instr(ins[n], 'ps'))
print('----- scan c54 su Xbox var0')
xrows = {e['slot']: (e['tex'], True) for e in C.entries(*DM[mid], 'be')}; STRAND[0] = 6610
XPm = F10.params(F10.f9_common._Sec(*DM[mid]), 'be')
xatt = {c['reg'] for c in XL.parse(xblob).ctab if c['set'] == 3 and 'Attenuation' in c['name']}
def meas(v54, c0):
    e = env_for(11, XPm, 1.0, 2.0, Kc, True); e.consts[54] = np.array(v54, np.float32); e.consts[0] = np.array([c0] * 4, np.float32)
    c, m, k = runp(px, e, xrows, None, xatt); mm = m > .25
    a = c[:, :3] * np.clip(c[:, 3:4], 0, 1); return a[mm].mean(), c[mm, 3].mean()
for v54 in [(0, 0, 0, 0), (1, 1, 1, 1), (.987654,) * 4, (0, 0, .987654, 0), (-1, -1, -1, -1), (100, 100, 100, 100), (0, 1, 0, 0), (1, 0, 0, 0), (0, 0, 0, 1)]:
    print(v54, 'c0=0:', np.round(meas(v54, 0.0), 3), 'c0=1:', np.round(meas(v54, 1.0), 3))
print('----- scrittori di r0.x')
for n, i in enumerate(ins):
    t = sm3asm.fmt_instr(i, 'ps')
    if t.split(' ', 1)[-1].startswith('r0.') and 'x' in t.split(' ', 1)[-1].split(',')[0] or (n < 40 and 'c' in t and ('c0.' in t or 'c54' in t or 'c64' in t or 'c65' in t)): print(n, t)
print('----- traccia r16/r14')
for n in range(440, 490): print(n, sm3asm.fmt_instr(ins[n], 'ps'))
