import sys; sys.path.insert(0,'/path/to/trudlcport/work/ws/codefirst')
from task3_validate import *
xs,pd=1409,1038
res,ties=mp_resolve.resolve(xs,pd)
print({k:v for k,v in res.items()})
for A in (0.0,1.0,2.0):
  for B in (0.0,1.0,2.0):
    r2=dict(res); r2[(108,3)]=('const',A); r2[(110,0)]=('const',B)
    o,info,n=one_pair(164,207,xs,pd,r2)
    print('A',A,'B',B,{k:round(v,3) for k,v in o.items()},flush=True)
