import sys
sys.path.insert(0,'/path/to/trudlcport/tools')
import param_auto as PA, difflib
L=PA.libs(); X,D=L['X'],L['D']
da=D[2299]['entries'][D[2299]['slots'][0]]['blob']; db=X[1201]['entries'][X[1201]['slots'][0]]['blob']
qa=PA.param_range(da); qb=PA.param_range(db); print(qa,qb)
ta=PA.tokens(da,*qa); tb=PA.tokens(db,*qb)
sm=difflib.SequenceMatcher(None,[t for t,_ in ta],[t for t,_ in tb],autojunk=False)
for tag,i1,i2,j1,j2 in sm.get_opcodes()[:14]:
    print(tag,i1,i2,j1,j2)
    if tag!='equal':
        for t in ta[i1:i1+3]: print('  A',t[0][:1],dict(t[0][1:]) if t[0][0]=='alu' else t[0], t[1])
        for t in tb[j1:j1+3]: print('  B',t[0][:1],dict(t[0][1:]) if t[0][0]=='alu' else t[0], t[1])
