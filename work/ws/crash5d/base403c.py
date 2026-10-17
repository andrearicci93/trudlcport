import sys,struct,collections
sys.path.insert(0,'/path/to/trudlcport/tools')
import dtpid_sweep as DS, dtp_audit as A
st,ids=DS.ctx(); cnt=collections.Counter(); vals=collections.Counter(); n=0; ex=[]; dtps=set()
for (t,x),xb in st['xb_store'].items():
    if t!=7: continue
    xd=xb['data']; p=ids.base[7].get(x); pc=st['pc_store'].get((7,p)) if p is not None else None
    if pc is None or len(pc['data'])!=len(xd): continue
    pd=pc['data']
    for o in range(0,len(xd)-0x34,4):
        if struct.unpack_from('>IIII',xd,o)==(0x403,0,0,0x30000):
            n+=1; dtps.add(x)
            xw=xd[o+0x30:o+0x34]; pw=pd[o+0x30:o+0x34]
            cnt[A.NAMES[[i for i,pp in enumerate(A.PERMS.values()) if bytes(xw[j] for j in pp)==pw][0]] if any(bytes(xw[j] for j in pp)==pw for pp in A.PERMS.values()) else 'other']+=1
            v=struct.unpack('>I',xw)[0]; vals[v if v<0x10000 else 'big']+=1
            if struct.unpack_from('<I',pd,o+0x30)[0]!=v and len(ex)<10: ex.append((x,hex(o),xw.hex(),pw.hex()))
print('base records',n,'in',len(dtps),'DTP; class of +0x30:',dict(cnt)); print('values',sorted(vals.items(),key=lambda kv:str(kv[0]))[:40]); print(ex)
