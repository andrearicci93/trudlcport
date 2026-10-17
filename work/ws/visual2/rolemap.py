"""rolemap.py - mappa MaterialParams D->S per firma di ruolo. uso: rolemap.py DLIB SLIB [oracle]"""
import sys,collections
sys.path.insert(0,'/path/to/trudlcport/work/ws/visual2')
import roles as RO, xenos_xlat as X
def informative(c):
    return frozenset(r for r in c if r[0] in ('uv','mul','add'))
def pair_maps(dl,sl):
    L=X.load_libs(); D,Xl=L['D'],L['X']
    ld=D.get(dl) or Xl[dl]; ls=Xl[sl]
    votes=collections.defaultdict(collections.Counter)   # S comp -> D comp votes
    sref=set(); dref=set(); nslots=0
    for si,(sa,sb) in enumerate(zip(ld['slots'],ls['slots'])):
        if sa==0xffffffff or sb==0xffffffff: continue
        shd,ird,rd=RO.analyse(ld['entries'][sa]['blob']); shs,irs,rs=RO.analyse(ls['entries'][sb]['blob'])
        nslots+=1
        # alias dei sampler senza controparte per nome: se per una dimensione resta 1 solo sampler non abbinato per lato, si abbinano
        ud={n:d for n,d in rd.snames.items() if n not in rs.snames}; us={n:d for n,d in rs.snames.items() if n not in rd.snames}
        alias={}
        for dim in set(ud.values())|set(us.values()):
            a=[n for n,d in ud.items() if d==dim]; b=[n for n,d in us.items() if d==dim]
            if len(a)==1 and len(b)==1: alias[a[0]]=b[0]
        if alias: rd=rd.renamed(alias)
        sigD=collections.defaultdict(list); sigS=collections.defaultdict(list)
        for k,c in rd.items():
            s=informative(c)
            if s: sigD[s].append(k)
        for k,c in rs.items():
            s=informative(c)
            if s: sigS[s].append(k)
        sref|=set(rs); dref|=set(rd)
        for s,ks in sigS.items():
            kd=sigD.get(s)
            if kd and len(kd)==len(ks) and (len(ks)==1 or (len({k[0] for k in ks})==1 and len({k[0] for k in kd})==1)):
                for a,b in zip(sorted(ks),sorted(kd)): votes[a][b]+=1
    return votes,sref,dref,nslots
if __name__=='__main__':
    dl,sl=int(sys.argv[1]),int(sys.argv[2])
    votes,sref,dref,ns=pair_maps(dl,sl)
    print('slots',ns,'S comps referenced',len(sref),'mapped',len(votes),'conflicting',sum(1 for c in votes.values() if len(c)>1))
    if len(sys.argv)>3:
        sys.path.insert(0,'/path/to/trudlcport/tools'); import param_remap as PR
        ok=bad=nov=0
        for s in sorted(sref):
            hand=PR.MAP_2299_TO_1201[s[0]][s[1]]
            c=votes.get(s)
            if not c: nov+=1; continue
            got=next(iter(c)) if len(c)==1 else None
            if got==hand: ok+=1
            else: bad+=1; print(' DIFF S',s,'hand',hand,'role',dict(c))
        print('oracle: equal',ok,'diff',bad,'no-vote',nov)
    else:
        for s in sorted(votes): print('S',s,'<- D',dict(votes[s]))
