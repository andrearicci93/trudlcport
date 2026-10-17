"""reader per dump dd_B5_2 a2 (directory vuota: ricostruito scansionando)"""
import struct,bisect
P='/path/to/trudlcport/work/runs/dd_B5_2/dumps/a2_tru.exe.1520.dmp'
F=open(P,'rb')
import os;SZ=os.path.getsize(P)
O=204771
F.seek(O+16); _d=F.read(16*200000)
c=0; _pa=-1
while c<200000:
    a,s_=struct.unpack_from('<QQ',_d,16*c)
    if a<=_pa or a>0x80000000 or a%4096 or s_%4096: break
    _pa=a; c+=1
b=O+16+16*c
d=_d[:16*c]
o=O
RG=[];pos=b
for i in range(c):
    a,s=struct.unpack_from('<QQ',d,16*i); RG.append((a,s,pos)); pos+=s
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
if __name__=='__main__':
    print(o,c,b,len(RG),pos)
