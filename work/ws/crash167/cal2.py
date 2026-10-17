import sys,pickle,struct,collections,math
sys.path.insert(0,'/path/to/trudlcport/tools')
import generic_ids as GI
P=pickle.load(open('/path/to/trudlcport/work/generic/pairs.pkl','rb'))
MK=b'\xbe\xeb\xbe\xeb'
def u16(w): return w[1::-1]+w[3:1:-1]
def u32(w): return w[::-1]
def portal_recs(xd):
    """aligned marker positions m where normal at m+8.. is unit (BE floats), -> list m"""
    out=[];m=xd.find(MK)
    while m>=0:
        if m%4==0 and m>=8 and m+0x20<=len(xd):
            n=struct.unpack_from('>3f',xd,m+8)
            l=math.sqrt(sum(x*x for x in n)) if all(abs(x)<2 for x in n) else 0
            if abs(l-1)<1e-3: out.append(m)
        m=xd.find(MK,m+1)
    return out
def classify(xw,pw):
    return 'u16' if pw==u16(xw) else 'u32' if pw==u32(xw) else 'raw' if pw==xw else 'other'
if __name__=='__main__':
    cnt=collections.Counter(); ex=collections.defaultdict(list); nrec=0
    for nm,v in P.items():
        (xh,sx),(ph,sp)=v
        try: ms=list(GI.section_matches(sx,sp,None))
        except Exception: continue
        for i,j,stg in ms:
            a,b=sx[i],sp[j]
            if a['type']!=0 or a['data'] is None or b['data'] is None or len(a['data'])!=len(b['data']): continue
            xd=a['data'];pd=b['data']
            for m in portal_recs(xd):
                xw=xd[m-4:m];pw=pd[m-4:m]; k=classify(xw,pw); cnt[k]+=1
                lo=struct.unpack('>H',xw[2:])[0]
                if k!='u16' and len(ex[k])<8: ex[k].append((nm,i,hex(m-4),xw.hex(),pw.hex()))
    print(cnt); print(dict(ex))
