import struct,bisect,sys
P='/path/to/trudlcport/work/runs/dd_B6_2/dumps/a1_tru.exe.11156.dmp'
F=open(P,'rb')
h=F.read(32)
sig,ver,n,dirrva=struct.unpack_from('<IIII',h,0)
F.seek(dirrva)
S={}
for i in range(n):
    t,sz,rva=struct.unpack('<III',F.read(12)); S[t]=(sz,rva); 
if __name__=='__main__':
    print(n,S)
