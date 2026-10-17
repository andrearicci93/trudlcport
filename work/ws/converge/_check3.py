import sys
sys.path.insert(0, '/path/to/trudlcport/tools')
import drm_write as DW
W='/path/to/trudlcport/work/ws/'
fresh=W+'rebuild/out_fresh2/'; post=W+'converge/out_post/'; refs=W+'refs/out/'
def secs(p): return DW.read(open(p,'rb').read(),'le').sections
for rel in ['dlc_dungeon.drm','dlc_dungeonhalla.drm','dlc_dungeonhallb.drm','dlc_treasureroom.drm','dlc_pillory.drm','dlc_watertunnel.drm']:
    F=secs(fresh+rel); P=secs(post+rel)
    R=secs(refs+rel) if __import__('os').path.exists(refs+rel) else None
    tot=0; agree=0; dis=[]; rdiff_only=0
    for k,(a,b) in enumerate(zip(F,P)):
        if bytes(a.data)==bytes(b.data): continue
        for q in range(0,len(a.data),4):
            if a.data[q:q+4]!=b.data[q:q+4]:
                tot+=1
                if R and k<len(R):
                    if bytes(R[k].data[q:q+4])==bytes(b.data[q:q+4]): agree+=1
                    else: dis.append((k,a.type,a.id,hex(q),bytes(a.data[q:q+4]).hex(),bytes(b.data[q:q+4]).hex(),bytes(R[k].data[q:q+4]).hex()))
    print(rel,'fresh->post words',tot,'agree with refs',agree,'disagree',len(dis))
    for d in dis[:8]: print('   ',d)
