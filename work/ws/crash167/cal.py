import sys,pickle,struct,collections
sys.path.insert(0,'/path/to/trudlcport/tools')
import generic_ids as GI, dtp_audit as A
P=pickle.load(open('/path/to/trudlcport/work/generic/pairs.pkl','rb'))
MK=b'\xbe\xeb\xbe\xeb'
def u16(w): return w[1::-1]+w[3:1:-1]
def u32(w): return w[::-1]
cnt=collections.Counter(); ex=collections.defaultdict(list)
for nm,v in P.items():
    (xh,sx),(ph,sp)=v
    try: ms=list(GI.section_matches(sx,sp,None))
    except Exception as e: continue
    for i,j,stg in ms:
        a,b=sx[i],sp[j]
        if a['type']!=0 or a['data'] is None or b['data'] is None or len(a['data'])!=len(b['data']): continue
        xd=a['data'];pd=b['data']
        m=xd.find(MK)
        while m>=4:
            xw=xd[m-4:m];pw=pd[m-4:m]
            # portal-like: next 4 words after marker: id then plane normal
            k='u16' if pw==u16(xw) else 'u32' if pw==u32(xw) else 'raw' if pw==xw else 'other'
            lo=struct.unpack('>H',xw[2:])[0]; hi=struct.unpack('>H',xw[:2])[0]
            cnt[(k, 'lo<=0x40' if lo<=0x40 else 'lo>0x40', 'hi<0x200' if hi<0x200 else 'hi big')]+=1
            if len(ex[k])<5: ex[k].append((nm,i,hex(m-4),xw.hex(),pw.hex()))
            m=xd.find(MK,m+1)
for k,v in sorted(cnt.items(),key=lambda x:-x[1]): print(k,v)
for k,v in ex.items(): print(k,v)
