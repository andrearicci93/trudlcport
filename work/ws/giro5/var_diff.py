import sys, io, contextlib, difflib
sys.path.insert(0, '/path/to/trudlcport/work/ws/giro5')
with contextlib.redirect_stdout(io.StringIO()):
    import build_unlit as B
L = B.libs(); D = L['D']
for dl in (2090, 2205):
    ts = []
    for k in (0, 1):
        blob = D[dl]['entries'][D[dl]['slots'][k]]['blob']
        K = B.Consts([]); t = B.xenos2sm3.translate(blob, K.fn, bools=None, samp=lambda n, c: c, opts={}); ts.append(t.text.splitlines())
    print('=== lib', dl, 'righe', len(ts[0]), len(ts[1]))
    for l in difflib.unified_diff(ts[0], ts[1], 'var0', 'var1', lineterm='', n=1): print(l)
