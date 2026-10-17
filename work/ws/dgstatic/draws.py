import sys, os, struct, collections
sys.path.insert(0,'/path/to/trudlcport/tools')
import drm, drm_reloc as R
W='/path/to/trudlcport/work/'
def secs(p,e):
    raw=drm.cdrm_decode(open(p,'rb').read(),e); return drm.sections_with_data(raw,e)[1]
def lists(s,e):
    E='>' if e=='be' else '<'; out={}
    for i,x in enumerate(s):
        if x['type']!=7 or not x['data']: continue
        d=x['data']; n=len(d)
        if n<20 or (n-4)%16: continue
        k=struct.unpack_from(E+'I',d,0)[0]
        if k==0 or n!=4+16*k: continue
        try: rel=R.parse(x['reloc'],e)
        except Exception: continue
        ids=list(rel.idref)+list(rel.idref_a)
        if sorted(ids)!=[(12,4+16*j) for j in range(k)]: continue
        out[i]=(k,[struct.unpack_from(E+'I',d,4+16*j+12)[0] for j in range(k)], [struct.unpack_from(E+'I',d,4+16*j+4)[0] for j in range(k)])
    return out
tot=collections.Counter()
for u in ['dlc_dungeon','dlc_watertunnel','dlc_treasureroom','dlc_dungeonhalla','dlc_dungeonhallb']:
    xs=secs(W+'ws/dgstatic/xbox/%s.drm'%u,'be'); ps=secs(W+'baseline/B8/mods/%s.drm'%u,'le')
    xl=lists(xs,'be'); pl=lists(ps,'le')
    same_keys=set(xl)==set(pl)
    cntdiff=[i for i in xl if i in pl and xl[i][0]!=pl[i][0]]
    midiff=[i for i in xl if i in pl and xl[i][0]==pl[i][0] and xl[i][1]!=pl[i][1]]
    print('%-18s draw-lists X %d PC %d sameSectionSet=%s  total draws X %d PC %d  count-mismatch %d  matIdx-mismatch %d'%(u,len(xl),len(pl),same_keys,sum(v[0] for v in xl.values()),sum(v[0] for v in pl.values()),len(cntdiff),len(midiff)))
    for i in midiff[:5]: print('   sec',i,'X',xl[i][1][:8],'PC',pl[i][1][:8])
    # section-level id equality of ids? type 7 ids
