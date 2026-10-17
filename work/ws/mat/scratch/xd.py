import sys,pickle,struct,collections
sys.path.insert(0,'/path/to/trudlcport/tools')
L=pickle.load(open('/path/to/trudlcport/work/render/shaderlibs.pkl','rb'))
X,D,P=L['X'],L['D'],L['P']
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
EXECS=(1,2,3,4,5,6,13,14)
def program(blob):
    w=getuc(blob); C=cfs(w)
    out=[]; m=10**9
    for k,c in enumerate(C):
        if k>=2*m: break
        op=(c>>44)&15
        if op in EXECS:
            a=c&0xfff; m=min(m,a)
            out.append((k,op,a,(c>>12)&7,(c>>16)&0xfff,c))
        else: out.append((k,op,None,None,None,c))
        if op==0 and c==0 and k>0 and False: pass
    return w,out
if __name__=='__main__':
    lib=X[int(sys.argv[1])]; s=lib['slots'][int(sys.argv[2])] if False else [s for s in lib['slots'] if s!=0xffffffff][int(sys.argv[2])]
    w,pr=program(lib['entries'][s]['blob'])
    for k,op,a,n,seq,c in pr:
        if a is None: continue
        for j in range(n):
            d0,d1,d2=w[3*(a+j):3*(a+j)+3]
            if (seq>>(2*j))&1: continue
            sc=(d0>>26)&63
            if sc in tuple(range(42,48)): print(a+j,'sopc',sc,'d0 %08x d1 %08x d2 %08x'%(d0,d1,d2))
