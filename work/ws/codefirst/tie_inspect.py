import sys; sys.path.insert(0,'/path/to/trudlcport/work/ws/codefirst')
from mp_cands import *
xs,pd=int(sys.argv[1]),int(sys.argv[2])
pl=[tuple(map(int,a.split('.'))) for a in sys.argv[3].split(',')]; xl=[tuple(map(int,a.split('.'))) for a in sys.argv[4].split(',')]
M=members(xs,pd)
print('PC lanes',pl,'Xbox lanes',xl)
for s in M:
    pv=[sorted({round(float(val(s['PP'],a)),4) for a in inv_alt(s['pmap'],s['pcls'],l) if val(s['PP'],a) is not None}) for l in pl]
    xv=[sorted({round(float(val(s['XP'],b)),4) for b in inv_alt(s['xmap'],s['xcls'],x) if val(s['XP'],b) is not None}) for x in xl]
    print(s['tag'],'PC',pv,'X',xv)
