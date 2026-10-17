import sys, struct, collections, os
sys.path.insert(0,'/path/to/trudlcport/tools')
import drm, unit_ids as U, objlists as OL
W='/path/to/trudlcport/work/'
def objs(p):
    return OL.read_objectlist(open(p,'rb').read())
XO=objs(W+'dlc1/objectlist.txt'); PO=objs(W+'baseline/B8/mods/tr8/pc-w/objectlist.txt')
def load(path,e):
    raw=drm.cdrm_decode(open(path,'rb').read(),e)
    return drm.sections_with_data(raw,e)[1]
def intros(path,e):
    secs=load(path,e); L=U.level_info(secs,e); E='>' if e=='be' else '<'
    out=[]
    for si,o in L['intros']:
        d=secs[si]['data']
        f=struct.unpack_from(E+'4f',d,o); oid=struct.unpack_from(E+'H',d,o+0x50)[0]; uid=struct.unpack_from(E+'I',d,o+0x58)[0]
        out.append((uid,oid,f,o))
    return out,L,secs
if __name__=='__main__':
    res={}
    for u in ['dlc_dungeon','dlc_watertunnel','dlc_treasureroom','dlc_dungeonhalla','dlc_dungeonhallb','dlc_pillory']:
        xp=W+'ws/dgstatic/xbox/%s.drm'%u; pp=W+'baseline/B8/mods/%s.drm'%u
        if not os.path.exists(pp): print(u,'no PC'); continue
        xi,XL,xs=intros(xp,'be'); pi,PL,ps=intros(pp,'le')
        xc=collections.Counter(XO.get(o,'?%d'%o) for _,o,_,_ in xi); pc=collections.Counter(PO.get(o,'?%d'%o) for _,o,_,_ in pi)
        print('=== %s: Xbox intros %d  PC intros %d  | tgs X %d PC %d | portals X %d PC %d'%(u,len(xi),len(pi),len(XL['tgs']),len(PL['tgs']),XL['npor'],PL['npor']))
        for n in sorted(set(xc)|set(pc)):
            print('  %-40s X=%-3d PC=%-3d %s'%(n,xc[n],pc[n],'' if xc[n]==pc[n] else '  <<< DIFF'))
        # position match by uid
        xm={ (round(f[0],2),round(f[1],2),round(f[2],2),XO.get(o)) for _,o,f,_ in xi}
        pm={ (round(f[0],2),round(f[1],2),round(f[2],2),PO.get(o)) for _,o,f,_ in pi}
        print('  position/name multiset: only-Xbox %d only-PC %d common %d'%(len(xm-pm),len(pm-xm),len(xm&pm)))
        for t in sorted(xm-pm)[:10]: print('   onlyX',t)
        for t in sorted(pm-xm)[:10]: print('   onlyPC',t)
