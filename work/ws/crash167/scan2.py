import sys,glob,struct,collections,difflib,json
sys.path.insert(0,'/path/to/trudlcport/tools');sys.path.insert(0,'/path/to/trudlcport/work/ws/crash167')
import fnd, soundplex_fix as S, cal2
BASE='/path/to/trudlcport/work/baseline/B6/mods/'
def pair0(xs,secs):
    xi=[k for k,x in enumerate(xs) if x['type']==0 and x['data'] is not None]
    pi=[k for k,s in enumerate(secs) if s['type']==0]
    xk=[(len(xs[k]['data']),xs[k]['data'].count(cal2.MK)) for k in xi]
    pk=[(len(secs[k]['data']),secs[k]['data'].count(b'\xeb\xbe\xeb\xbe')) for k in pi]
    sm=difflib.SequenceMatcher(None,xk,pk,autojunk=False)
    out=[]
    for a,b,n in sm.get_matching_blocks():
        for t in range(n): out.append((xi[a+t],pi[b+t]))
    return out,len(pi),len(out)
def scan(base=BASE):
    res=[];tot=collections.Counter();unp=[]
    for p in sorted(glob.glob(base+'**/*.drm',recursive=True)):
        rel=p.split('mods/')[1]
        try: xs=S.xsecs_of(rel)
        except Exception: continue
        if not xs: continue
        try: h,secs=fnd.load(p)
        except Exception: continue
        pr,n0,nm=pair0(xs,secs)
        if nm<n0: unp.append((rel,n0,nm))
        for xk,pk in pr:
            xd=xs[xk]['data'];pd=secs[pk]['data']
            for m in cal2.portal_recs(xd):
                xw=xd[m-4:m];pw=pd[m-4:m];c=cal2.classify(xw,pw);tot[c]+=1
                if c!='u16': res.append((rel,xk,pk,secs[pk]['i'],m-4,xw.hex(),pw.hex(),c))
    return res,tot,unp
if __name__=='__main__':
    res,tot,unp=scan()
    print(tot)
    print('unpaired type0',unp)
    for r in res: print(r)
    json.dump(res,open('scan2_B6.json','w'))
