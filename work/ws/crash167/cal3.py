import sys,pickle,struct,collections
sys.path.insert(0,'/path/to/trudlcport/tools');sys.path.insert(0,'/path/to/trudlcport/work/ws/crash167')
import generic_ids as GI, cal2
P=pickle.load(open('/path/to/trudlcport/work/generic/pairs.pkl','rb'))
MK=cal2.MK
def chain_recs(xd,minrun=2):
    pos=[];m=xd.find(MK)
    while m>=0:
        if m%4==0 and m>=8: pos.append(m)
        m=xd.find(MK,m+1)
    S=set(pos); out=[]
    for m in pos:
        if (m+0x40 in S) or (m-0x40 in S): out.append(m)
    return out
if __name__=='__main__':
    cnt=collections.Counter(); ex=collections.defaultdict(list)
    for nm,v in P.items():
        (xh,sx),(ph,sp)=v
        try: ms=list(GI.section_matches(sx,sp,None))
        except Exception: continue
        for i,j,stg in ms:
            a,b=sx[i],sp[j]
            if a['type']!=0 or a['data'] is None or b['data'] is None or len(a['data'])!=len(b['data']): continue
            xd=a['data'];pd=b['data']
            for m in chain_recs(xd):
                xw=xd[m-4:m];pw=pd[m-4:m];k=cal2.classify(xw,pw)
                lo=struct.unpack('>H',xw[2:])[0];hi=struct.unpack('>H',xw[:2])[0]
                cnt[(k)]+=1
                if k!='u16' and len(ex[k])<6: ex[k].append((nm,i,hex(m-4),xw.hex(),pw.hex()))
    print(cnt);print(dict(ex))
