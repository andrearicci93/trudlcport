"""portal pair words in type-0 cell sections: Xbox BE {u16 start, u16 count} at (marker 0xbeebbeeb)-4 -> PC must be u16-pair swap.
Rule: 4-aligned marker be eb be eb with another marker at +-0x40 (record array), BE hi,lo both in 1..0x3ff.
CLI: scan [base] | selftest | build"""
import sys,struct,glob,collections,pickle,difflib
sys.path.insert(0,'/path/to/trudlcport/tools');sys.path.insert(0,'/path/to/trudlcport/work/ws/crash167')
MK=b'\xbe\xeb\xbe\xeb'
def want_word(xw): return xw[1::-1]+xw[3:1:-1]
def cands(xd):
    pos=[];m=xd.find(MK)
    while m>=0:
        if m%4==0 and m>=4: pos.append(m)
        m=xd.find(MK,m+1)
    S=set(pos)
    for m in pos:
        if (m+0x40 in S) or (m-0x40 in S):
            hi,lo=struct.unpack('>HH',xd[m-4:m])
            if 0<hi<0x400 and 0<lo<0x400: yield m-4
def fix_section(xd,pd):
    """-> (new pd, [(off,old,new)])"""
    b=bytearray(pd);ch=[]
    for o in cands(xd):
        w=want_word(xd[o:o+4])
        if bytes(b[o:o+4])!=w: ch.append((o,bytes(b[o:o+4]),w)); b[o:o+4]=w
    return bytes(b),ch
def selftest():
    import generic_ids as GI
    P=pickle.load(open('/path/to/trudlcport/work/generic/pairs.pkl','rb'))
    n=nc=0;fp=[]
    for nm,v in P.items():
        (xh,sx),(ph,sp)=v
        try: ms=list(GI.section_matches(sx,sp,None))
        except Exception: continue
        for i,j,stg in ms:
            a,b=sx[i],sp[j]
            if a['type']!=0 or a['data'] is None or b['data'] is None or len(a['data'])!=len(b['data']): continue
            n+=1; nd,ch=fix_section(a['data'],b['data']); nc+=len(ch)
            fp+= [(nm,i,hex(o),old.hex(),new.hex()) for o,old,new in ch]
    print('base type0 sections',n,'words changed',nc); print(fp[:10])
def scan(base='/path/to/trudlcport/work/baseline/B6/mods/'):
    import fnd, soundplex_fix as S, scan2
    out=[]
    for p in sorted(glob.glob(base+'**/*.drm',recursive=True)):
        rel=p.split('mods/')[1]
        try: xs=S.xsecs_of(rel); h,secs=fnd.load(p)
        except Exception: continue
        if not xs: continue
        pr,_,_=scan2.pair0(xs,secs)
        for xk,pk in pr:
            nd,ch=fix_section(xs[xk]['data'],secs[pk]['data'])
            for o,old,new in ch: out.append((rel,secs[pk]['i'],o,old,new))
    return out
if __name__=='__main__':
    if sys.argv[1]=='selftest': selftest()
    if sys.argv[1]=='scan':
        for r in scan(): print(r[0],'sec',r[1],hex(r[2]),r[3].hex(),'->',r[4].hex())
