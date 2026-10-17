import sys,struct;sys.path.insert(0,'/path/to/trudlcport/work/ws/crash167');sys.path.insert(0,'/path/to/trudlcport/tools')
import fnd, soundplex_fix as S
rel='dlc_dungeon.drm'
P='/path/to/trudlcport/work/baseline/B6/mods/'+rel
h,secs=fnd.load(P); xs=S.xsecs_of(rel)
print(len(secs),len(xs))
s=[x for x in secs if x['i']==47][0]; x=xs[47]
print(x['type'],len(x['data']),len(s['data']))
xd=x['data'];pd=s['data']
i=pd.find(b'\xeb\xbe\xeb\xbe')
while i>=0:
    print(hex(i-4),'PC',pd[i-4:i].hex(),'XB',xd[i-4:i].hex(),'marker xb',xd[i:i+4].hex())
    i=pd.find(b'\xeb\xbe\xeb\xbe',i+1)
