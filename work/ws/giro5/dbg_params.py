import sys,io,contextlib,json,struct
sys.path.insert(0,'/path/to/trudlcport/work/ws/giro5')
with contextlib.redirect_stdout(io.StringIO()):
    import build_unlit as B
import numpy as np
F9=B.F14.F9;F10=B.F14.F10;C=B.F14.C
mid=int(sys.argv[1]); rel=sys.argv[2]
L=B.libs();DM=L['DM']
t=C.read_tree(B.BASE); ms={(s.type,s.id):s for s in t[rel].sections}[(10,mid)]
XP=F10.params(F10.f9_common._Sec(*DM[mid]),'be'); PP=F10.params(ms,'le')
print('len X',len(XP),'len P',len(PP))
for j in range(max(len(XP),len(PP))):
    a=XP[j] if j<len(XP) else None; b=PP[j] if j<len(PP) else None
    print(j, None if a is None else np.round(np.array(a,float),4), None if b is None else np.round(np.array(b,float),4), '' if (a is not None and b is not None and np.allclose(a,b,atol=1e-4)) else '<<< DIVERSO')
