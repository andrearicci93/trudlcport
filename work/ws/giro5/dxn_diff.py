import sys, io, contextlib, difflib
sys.path.insert(0, '/path/to/trudlcport/work/ws/giro5')
with contextlib.redirect_stdout(io.StringIO()):
    import build_unlit as B
L = B.libs(); D = L['D']; F9 = B.F14.F9
for k in (0, 1):
    blob = D[2166]['entries'][D[2166]['slots'][k]]['blob']
    ts = []
    for o in ({}, {'dxn': {8}}):
        K = F9.Consts([]); ts.append(F9.translate_x(blob, K.fn, lambda n, c: c, F9.xbools(blob), opts=o)[3].text.splitlines())
    d = [l for l in difflib.unified_diff(ts[0], ts[1], lineterm='', n=0) if not l.startswith(('---', '+++', '@@'))]
    print('slot Xbox', k, 'righe diverse con dxn su reg 8:', len(d)); print('\n'.join(d[:14]))
