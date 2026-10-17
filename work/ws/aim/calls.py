import sys,struct
from xdis import *
def callers(t):
    out=[]
    for a,s,rp,rs in S[:1]:
        d=E[rp:rp+rs]
        for i in range(len(d)-5):
            if d[i] in (0xe8,0xe9):
                r=struct.unpack_from('<i',d,i+1)[0]
                if (a+i+5+r)&0xffffffff==t: out.append(a+i)
    return out
def fstart(va):
    # back up to previous int3 run
    d=rd(va-0x1000,0x1000)
    i=len(d)-1
    while i>0:
        if d[i]==0xcc and d[i+1]!=0xcc: return va-0x1000+i+1 if False else None
        i-=1
if __name__=='__main__':
    for t in sys.argv[1:]: print(t,[hex(x) for x in callers(int(t,16))], 'vtable-refs:')
