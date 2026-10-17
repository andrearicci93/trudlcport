import sys,io,contextlib
sys.path.insert(0,'/path/to/trudlcport/work/ws/giro5')
with contextlib.redirect_stdout(io.StringIO()):
    import build_unlit as B
L=B.libs(); P=L['P']
vs=B.decode_pc(P[1088]['entries'][P[1088]['slots'][0]]['blob'])
for i in vs.instrs():
    if i.op=='dcl': print(i.op,i.ops[0].rtype,i.ops[0].num,hex(i.usage))
