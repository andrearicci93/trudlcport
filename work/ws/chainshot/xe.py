import sys,struct,capstone,re
E=open('/path/to/trudlcport/work/laa/tru_steam.exe.unpacked.exe','rb').read()
pe=struct.unpack_from('<I',E,0x3c)[0]; ns=struct.unpack_from('<H',E,pe+6)[0]; ob=struct.unpack_from('<H',E,pe+20)[0]
base=struct.unpack_from('<I',E,pe+0x34)[0]
S=[]
for i in range(ns):
    o=pe+24+ob+40*i; vs,va,rs,rp=struct.unpack_from('<IIII',E,o+8)
    nm=E[o:o+8].rstrip(b'\0').decode()
    S.append((va+base,max(vs,rs),rp,rs,nm))
def rd(va,n):
    for a,s,rp,rs,nm in S:
        if a<=va<a+s: return E[rp+va-a:rp+va-a+n]
    return b'\0'*n
def u32(va): return struct.unpack('<I',rd(va,4))[0]
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
def dis(va,n=0x100,out=True):
    r=[]
    for i in md.disasm(rd(va,n),va):
        r.append('%x: %s %s'%(i.address,i.mnemonic,i.op_str))
    if out: print('\n'.join(r))
    return r
def find_bytes(pat):
    res=[]
    for a,s,rp,rs,nm in S:
        d=E[rp:rp+rs]; i=d.find(pat)
        while i>=0:
            res.append(a+i); i=d.find(pat,i+1)
    return res
def refs(t):
    return find_bytes(struct.pack('<I',t))
def calls(t):
    """find E8 rel32 calls to t in text"""
    res=[]
    a,s,rp,rs,nm=S[0]
    d=E[rp:rp+rs]
    for m in re.finditer(b'[\xe8\xe9]',d):
        i=m.start()
        if i+5>len(d): continue
        rel=struct.unpack_from('<i',d,i+1)[0]
        if (a+i+5+rel)&0xffffffff==t: res.append(a+i)
    return res
def func_start(va):
    # crude: scan back for 'int3/ret' padding then plausible prologue
    d=rd(va-0x4000,0x4000)
    i=len(d)
    while i>0:
        i-=1
        if d[i:i+1] in (b'\xcc',) and d[i+1:i+2]!=b'\xcc': 
            return va-0x4000+i+1
    return None
if __name__=='__main__':
    dis(int(sys.argv[1],16),int(sys.argv[2],0) if len(sys.argv)>2 else 0x100)

def rtti(name):
    """find vtable(s) for class name e.g. 'UberObjectComposite_TR8'"""
    pat=b'.?AV'+name.encode()+b'@@\0'
    out=[]
    for td in find_bytes(pat):
        tdv=td-8
        # COLs: dword pointing to td at col+12
        for c in refs(tdv):
            col=c-12
            sig=u32(col)
            if sig!=0: continue
            for vt in refs(col):
                out.append((tdv,col,vt+4))
    return out
