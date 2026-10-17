import sys, collections, struct, pickle
sys.path.insert(0,'work/ws/fpfloat'); sys.path.insert(0,'tools')
from exp3 import *
from explore import pairs_for
import dtp_audit as A
# build stats for SoundPlex DTPs only (node0) at depth 1..3 (no shape), key=(k, rkey_d)
D=3
stat=[collections.defaultdict(lambda:[0]*6) for _ in range(D+1)]
nsp=0
for x,p,xb,pc,xr in A.base_pairs():
    xd=xb['data']; pd=pc['data']
    if not A.node0(xd,xr): continue
    nsp+=1
    for o,k,rk in ctx_words(xd,xr,D):
        c=cls(xd[o:o+4],pd[o:o+4])
        if c==A.ALL or c==0: continue
        for d in range(1,D+1):
            v=stat[d][(k,rk[d-1])]; v[0]+=1
            for i in range(5):
                if c>>i&1: v[i+1]+=1
print('soundplex base dtps',nsp)
pickle.dump([dict(s) for s in stat],open('work/ws/fpfloat/sp_stat.pkl','wb'))
# problem words
xs,Dd,prs=pairs_for('dlc1_uo_raft_bridge_spawned.drm')
for x,i in prs:
    sec=Dd.sections[i]
    if sec.id!=21222: continue
    xd=x['data'];pd=sec.data;rel=R.parse(x['reloc'],'be')
    cw={o:(k,rk) for o,k,rk in ctx_words(xd,rel,D)}
    for o in (0x20,0x300,0x324,0x2b0,0x5f8,0x6b4,0x4b8,0x4fc,0x2f8,0x3b0):
        if o not in cw: continue
        k,rk=cw[o]
        print(hex(o),xd[o:o+4].hex(),pd[o:o+4].hex())
        for d in range(1,D+1):
            v=stat[d].get((k,rk[d-1]))
            print('   depth',d,'k',hex(k),rk[d-1] if d<3 else '...', v)
