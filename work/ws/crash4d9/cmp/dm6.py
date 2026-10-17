import struct,bisect
P='/path/to/trudlcport/work/runs/dd_B6_2/dumps/a1_tru.exe.11156.dmp'
F=open(P,'rb')
F.seek(32);S={}
for i in range(17):
    t,sz,rva=struct.unpack('<III',F.read(12)); S[t]=(sz,rva)
F.seek(S[9][1]); cnt,base=struct.unpack('<QQ',F.read(16))
RG=[];pos=base
for i in range(cnt):
    a,s=struct.unpack('<QQ',F.read(16)); RG.append((a,s,pos)); pos+=s
ST=[r[0] for r in RG]
def rd(a,n):
    out=b''
    while n>0:
        i=bisect.bisect_right(ST,a)-1
        if i<0: return None
        ra,rs,rp=RG[i]
        if a>=ra+rs: return None
        k=min(n,ra+rs-a); F.seek(rp+a-ra); out+=F.read(k); a+=k; n-=k
    return out
def u32(a):
    b=rd(a,4); return struct.unpack('<I',b)[0] if b else None
def exc():
    F.seek(S[6][1]); tid,_=struct.unpack('<II',F.read(8))
    er=F.read(152); code,fl,rec,addr,np=struct.unpack_from('<IIQQI',er,0)
    info=struct.unpack_from('<15Q',er,32)
    ctxsz,ctxrva=struct.unpack('<II',F.read(8))
    F.seek(ctxrva); c=F.read(ctxsz)
    return tid,code,addr,info[:np],c
REG=['Edi','Esi','Ebx','Edx','Ecx','Eax','Ebp','Eip','SegCs','EFlags','Esp','SegSs']
def regs(c):
    v=struct.unpack_from('<12I',c,0x9c)
    return dict(zip(REG,v))
if __name__=='__main__':
    print(cnt,hex(base),len(RG),hex(ST[-1]))
    tid,code,addr,info,c=exc()
    print(tid,hex(code),hex(addr),[hex(x) for x in info])
    r=regs(c); print({k:hex(v) for k,v in r.items()})
