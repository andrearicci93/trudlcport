import sys,struct,capstone
from xdis import *
t=int(sys.argv[1],16)
pat=struct.pack('<I',t)
for a,s,rp,rs in S:
    d=E[rp:rp+rs]; i=0
    while True:
        i=d.find(pat,i)
        if i<0:break
        va=a+i
        print('%x'%va, d[max(0,i-3):i].hex(), d[i+4:i+8].hex()); i+=1
