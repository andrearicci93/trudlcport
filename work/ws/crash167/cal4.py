import sys,pickle,struct,collections
sys.path.insert(0,'/path/to/trudlcport/tools');sys.path.insert(0,'/path/to/trudlcport/work/ws/crash167')
import generic_ids as GI, cal2, cal3
P=pickle.load(open('/path/to/trudlcport/work/generic/pairs.pkl','rb'))
cnt=collections.Counter(); ex=[]
for nm,v in P.items():
    (xh,sx),(ph,sp)=v
    try: ms=list(GI.section_matches(sx,sp,None))
    except Exception: continue
    for i,j,stg in ms:
        a,b=sx[i],sp[j]
        if a['type']!=0 or a['data'] is None or b['data'] is None or len(a['data'])!=len(b['data']): continue
        xd=a['data'];pd=b['data']
        for m in cal3.chain_recs(xd):
            xw=xd[m-4:m];pw=pd[m-4:m];hi,lo=struct.unpack('>HH',xw)
            if hi and lo:
                k=cal2.classify(xw,pw); cnt[(k,'lo4' if lo==4 else 'lo!=4')]+=1
                if k!='u16' and len(ex)<10: ex.append((nm,i,hex(m-4),xw.hex(),pw.hex()))
print(cnt);print(ex)
