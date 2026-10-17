import sys,glob,struct,collections
sys.path.insert(0,'/path/to/trudlcport/tools');sys.path.insert(0,'/path/to/trudlcport/work/ws/crash167')
import fnd, soundplex_fix as S, cal2
BASE='/path/to/trudlcport/work/baseline/B6/mods/'
def scan(names=None, base=BASE):
    res=[];tot=collections.Counter()
    for p in sorted(glob.glob(base+'**/*.drm',recursive=True)):
        rel=p.split('mods/')[1]
        if names and rel not in names: continue
        try: xs=S.xsecs_of(rel)
        except Exception: continue
        if not xs: continue
        try: h,secs=fnd.load(p)
        except Exception: continue
        if len(xs)!=len(secs): tot['layout_mismatch']+=1; continue
        for k,(x,s) in enumerate(zip(xs,secs)):
            if x['type']!=0 or x['data'] is None or len(x['data'])!=len(s['data']): continue
            for m in cal2.portal_recs(x['data']):
                xw=x['data'][m-4:m]; pw=s['data'][m-4:m]; c=cal2.classify(xw,pw); tot[c]+=1
                if c!='u16': res.append((rel,k,s['i'],m-4,xw.hex(),pw.hex(),c))
    return res,tot
if __name__=='__main__':
    res,tot=scan()
    print(tot)
    c=collections.Counter(r[0] for r in res)
    for f,n in c.items(): print(f,n)
    import json;json.dump(res,open('scan_B6.json','w'))
