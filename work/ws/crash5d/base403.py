import sys,struct,collections
sys.path.insert(0,'/path/to/trudlcport/tools')
import dtp_audit as A
cnt=collections.Counter(); ex=[]
tot=0
for x,p,xb,pc,xr in A.base_pairs():
    xd=xb['data']; pd=pc['data']
    for o in range(0,len(xd)-0x34,4):
        if struct.unpack_from('>IIII',xd,o)==(0x403,0,0,0x300):
            tot+=1
            xw=xd[o+0x30:o+0x34]; pw=pd[o+0x30:o+0x34]
            c=A.cls(xw,pw); cnt[(c,)]+=1
            if len(ex)<12: ex.append((x,hex(o),xw.hex(),pw.hex()))
print(tot,dict(cnt)); print(ex)
