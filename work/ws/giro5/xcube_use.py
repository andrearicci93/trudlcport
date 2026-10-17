import sys, io, contextlib
sys.path.insert(0, '/path/to/trudlcport/work/ws/giro5')
with contextlib.redirect_stdout(io.StringIO()):
    import web_eval2 as W
F9 = W.F9; D = W.D
blob = D[2199]['entries'][D[2199]['slots'][0]]['blob']
t = F9.translate_x(blob, F9.Consts([]).fn, lambda n, c: c, F9.xbools(blob), opts={})[3].text.splitlines()
for i, l in enumerate(t):
    if 'texld' in l and l.strip().endswith(', s0'):
        print('\n'.join('%3d %s' % (j, t[j]) for j in range(max(0, i - 6), min(len(t), i + 22)))); break
