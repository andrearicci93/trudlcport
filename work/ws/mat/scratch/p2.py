import sys,pickle,struct,collections
sys.path.insert(0,'tools')
L=pickle.load(open('work/render/shaderlibs.pkl','rb'))
X,D=L['X'],L['D']
def getuc(blob):
    h=struct.unpack_from('>16I',blob,0); p=h[6]; a,sz=struct.unpack_from('>II',blob,p)
    uc=blob[len(blob)-8-sz:len(blob)-8]
    return struct.unpack('>%dI'%(len(uc)//4),uc)
def cfs(w):
    out=[]
    for i in range(0,len(w)-2,3):
        d0,d1,d2=w[i:i+3]
        out+=[d0|((d1&0xffff)<<32),(d1>>16)|(d2<<16)]
    return out
lib=X[1201]; b=lib['entries'][lib['slots'][0]]['blob']
w=getuc(b); C=cfs(w)
first=74
seen=0
for k,c in enumerate(C[:first*2]):
    op=(c>>44)&15
    if op in (1,2,3,4,5,6,13,14):
        a=c&0xfff; n=(c>>12)&7; seq=(c>>16)&0xfff
        for j in range(n):
            s=a+j; d0,d1,d2=w[3*s:3*s+3]
            fetch=(seq>>(2*j))&1
            if fetch:
                print('slot',s,'FETCH',hex(d0),hex(d1),hex(d2))
            else:
                v=(d2>>24)&31; sc=(d0>>26)&63
                s1,s2,s3=(d2>>31)&1,(d2>>30)&1,(d2>>29)&1
                print('slot',s,'ALU vopc',v,'sopc',sc,'sel',s1,s2,s3,'regs',d2&255,(d2>>8)&255,(d2>>16)&255,'swz',hex(d1&255),hex((d1>>8)&255),hex((d1>>16)&255),'d0',hex(d0),'d1b',hex(d1>>24))
        seen+=n
    if seen>40: break
