import sys,struct,collections,glob
sys.path.insert(0,'/path/to/trudlcport/tools');sys.path.insert(0,'/path/to/trudlcport/work/ws/crash167')
import fnd, soundplex_fix as S, cal2, scan2
BASE=scan2.BASE
c=collections.Counter()
for p in sorted(glob.glob(BASE+'**/*.drm',recursive=True)):
    rel=p.split('mods/')[1]
    try: xs=S.xsecs_of(rel); h,secs=fnd.load(p)
    except Exception: continue
    if not xs: continue
    pr,_,_=scan2.pair0(xs,secs)
    for xk,pk in pr:
        xd=xs[xk]['data'];pd=secs[pk]['data']
        m=xd.find(cal2.MK)
        while m>=0:
            if m%4==0 and m>=4:
                xw=xd[m-4:m];pw=pd[m-4:m]
                hi,lo=struct.unpack('>HH',xw)
                if hi and lo and cal2.classify(xw,pw)=='u32':
                    c[(rel,secs[pk]['i'])]+=1
            m=xd.find(cal2.MK,m+1)
print(c)
rel='dlc_dungeon.drm'
xs=S.xsecs_of(rel); h,secs=fnd.load(BASE+rel)
for k in (47,51):
    xd=xs[k]['data'];pd=secs[k]['data']; m=xd.find(cal2.MK)
    while m>=0:
        if m%4==0 and m>=4:
            xw=xd[m-4:m];pw=pd[m-4:m];hi,lo=struct.unpack('>HH',xw)
            if hi and lo and cal2.classify(xw,pw)=='u32': print(k,hex(m-4),xw.hex(),pw.hex(),m in cal2.portal_recs(xd), xd[m-12:m+0x20].hex())
        m=xd.find(cal2.MK,m+1)
