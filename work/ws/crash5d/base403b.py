import sys,struct,collections
sys.path.insert(0,'/path/to/trudlcport/tools')
import dtpid_sweep as DS
st,ids=DS.ctx()
n=0; per=collections.Counter(); ex=[]
for (t,x),xb in st['xb_store'].items():
    if t!=7: continue
    xd=xb['data']
    for o in range(0,len(xd)-0x34,4):
        if struct.unpack_from('>IIII',xd,o)==(0x403,0,0,0x300):
            n+=1; per[x]+=1
            p=ids.base[7].get(x); pc=st['pc_store'].get((7,p)) if p is not None else None
            if len(ex)<20: ex.append((x,p,hex(o),xd[o+0x30:o+0x34].hex(), pc['data'][o+0x30:o+0x34].hex() if pc and len(pc['data'])>o+0x34 else None))
print(n,dict(per)); print(*ex,sep='\n')
