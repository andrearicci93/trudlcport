import sys,struct,glob,collections
sys.path.insert(0,'/path/to/trudlcport/tools');sys.path.insert(0,'/path/to/trudlcport/work/ws/crash167')
import fnd, soundplex_fix as S, cal2, cal3, scan2
c=collections.Counter()
for p in sorted(glob.glob(scan2.BASE+'**/*.drm',recursive=True)):
    rel=p.split('mods/')[1]
    try: xs=S.xsecs_of(rel); h,secs=fnd.load(p)
    except Exception: continue
    if not xs: continue
    pr,_,_=scan2.pair0(xs,secs)
    for xk,pk in pr:
        xd=xs[xk]['data'];pd=secs[pk]['data']
        for m in cal3.chain_recs(xd):
            xw=xd[m-4:m];pw=pd[m-4:m];hi,lo=struct.unpack('>HH',xw)
            if hi<0x400 and lo<0x400 and xw!=b'\0\0\0\0':
                c[(rel if cal2.classify(xw,pw)!='u16' else 'ALL',cal2.classify(xw,pw),'hi0' if hi==0 else 'hi')]+=1
for k,v in sorted(c.items()): print(k,v)
print('---')
xs=S.xsecs_of('dlc_dungeon.drm'); h,secs=fnd.load(scan2.BASE+'dlc_dungeon.drm')
for k,(x,s) in enumerate(zip(xs,secs)):
    if x['type']!=0: continue
    xd=x['data'];pd=s['data']
    for m in cal3.chain_recs(xd):
        xw=xd[m-4:m];pw=pd[m-4:m];hi,lo=struct.unpack('>HH',xw)
        if hi==0 and 0<lo<0x400 and cal2.classify(xw,pw)=='u32': print(k,hex(m-4),xw.hex(),pw.hex(),'prev',xd[m-8:m-4].hex())
