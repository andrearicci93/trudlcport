import sys,struct; sys.path.insert(0,'C:/tru-port/tools'); import drm_write as DW
X=DW.read(open('C:/tru-port/work/dlc2/xbox/dlc2_goo_room.drm','rb').read(),'be').sections
P=DW.read(open('C:/tru-port/work/baseline/B273_typelist2/mods/dlc2_goo_room.drm','rb').read(),'le').sections
def sw(b,pat):  # pat: list of field sizes per record
    out=bytearray(); rl=sum(pat); n=len(b)//rl
    for r in range(n):
        o=r*rl
        for f in pat: out+=b[o:o+f][::-1]; o+=f
    return bytes(out)+b[n*rl:]
def cmp(i,pat):
    x,p=X[i].data,P[i].data; e=sw(x,pat); rl=sum(pat)
    bad=sorted({j//rl for j in range(min(len(e),len(p))) if e[j]!=p[j]})
    return bad
for i in range(2,9): b=cmp(i,[4]*4); print('vert',i,len(X[i].data)//16,'bad rec',len(b),b[:10])
for i in range(9,16): b=cmp(i,[4,4,4,1,1,2,4]); print('face',i,len(X[i].data)//20,len(X[i].data)%20,'bad rec',len(b),b[:10])
for i in range(16,23): b=cmp(i,[4]*4); print('tree',i,len(X[i].data)//16,len(X[i].data)%16,'bad rec',len(b),b[:10])
print('---')
from collections import Counter
for i in (9,11,15):
    x,p=X[i].data,P[i].data; e=sw(x,[4,4,4,1,1,2,4]); c=Counter()
    for r in range(len(x)//20):
        for f,(a,b) in enumerate(((0,4),(4,8),(8,12),(12,13),(13,14),(14,16),(16,20))):
            if e[r*20+a:r*20+b]!=p[r*20+a:r*20+b]: c[f]+=1
    print(i,c)
    for r in cmp(i,[4,4,4,1,1,2,4])[:4]: print('  X',x[r*20:r*20+20].hex(),'P',p[r*20:r*20+20].hex())
print('=== layout del convertitore')
def sw2(b,pat):
    out=bytearray(); rl=sum(abs(f) for f in pat); n=len(b)//rl
    for r in range(n):
        o=r*rl
        for f in pat:
            out+=b[o:o+abs(f)][::-1] if f>0 else b[o:o-f]; o+=abs(f)
    return bytes(out)+b[n*rl:]
for i in range(9,23):
    pat=[4,4,4,1,1,2,-4] if i<16 else [4,4,4,-4]; rl=20 if i<16 else 16
    x,p=X[i].data,P[i].data; e=sw2(x,pat)
    bad=sorted({j for j in range(len(p)) if e[j]!=p[j]})
    print(i,'righe',len(x)//rl,'byte diversi',len(bad),[hex(j) for j in bad[:8]], 'coda X',x[len(x)//rl*rl:].hex(),'P',p[len(x)//rl*rl:].hex())
