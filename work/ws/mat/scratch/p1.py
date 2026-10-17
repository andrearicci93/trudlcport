import sys,pickle,struct,collections
sys.path.insert(0,'tools')
L=pickle.load(open('work/render/shaderlibs.pkl','rb'))
X,D=L['X'],L['D']
def ucode(blob):
    n=struct.unpack_from('>I',blob,0x8fc)[0] if False else None
    return blob
def getuc(blob):
    # find ucode: header word[6] points to a block {u32 a,u32 size}
    h=struct.unpack_from('>16I',blob,0)
    p=h[6]; a,sz=struct.unpack_from('>II',blob,p)
    return a,sz
lib=X[1201]; b=lib['entries'][lib['slots'][0]]['blob']
a,sz=getuc(b); print(hex(a),hex(sz),len(b))
uc=b[len(b)-8-sz:len(b)-8]
w=struct.unpack('>%dI'%(len(uc)//4),uc)
# CF
cfs=[]
for i in range(0,len(w)-2,3):
    d0,d1,d2=w[i:i+3]
    c0=d0|((d1&0xffff)<<32); c1=(d1>>16)|(d2<<16)
    cfs+= [c0,c1]
    if i//3 >= 80: break
for k,c in enumerate(cfs[:160]):
    op=(c>>44)&0xf
    if op==0 and c==0: continue
    print(k,op,'addr',c&0xfff,'cnt',(c>>12)&7,'seq',hex((c>>16)&0xfff), hex(c))
