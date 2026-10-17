import sys; sys.path.insert(0,'/path/to/trudlcport/work/ws/codefirst')
from mp_resolve import *
xs,pd=int(sys.argv[1]),int(sys.argv[2])
res,ties=resolve(xs,pd)
M=members(xs,pd)
def exact(mp,lane):
    if mp is None: return lane
    s=[k for k,v in mp.items() if v==lane]; return s[0] if s else None
for l,cs in sorted(ties.items()):
    print('PC c%d.%s candidati'%(l[0],'xyzw'[l[1]]),cs)
    for x in cs:
        n=0;tot=0;det=[]
        for s in M:
            a=exact(s['pmap'],l); b=exact(s['xmap'],x)
            if a is None or b is None: continue
            va,vb=val(s['PP'],a),val(s['XP'],b)
            if va is None or vb is None: continue
            tot+=1; n+= abs(va-vb)<1e-6
            if abs(va-vb)>=1e-6: det.append((s['tag'][1:],round(float(va),3),round(float(vb),3)))
        print('   <- c%d.%s: %d/%d campioni uguali (esatto, senza simmetrie)'%(x[0],'xyzw'[x[1]],n,tot), det[:4])
