import sys,struct
sys.path.insert(0,'/path/to/trudlcport/tools')
import material_reslot as MR
L=MR.libs(); P=L['P']
OPN={1:'mov',2:'add',3:'sub',4:'mad',5:'mul',6:'rcp',7:'rsq',8:'dp3',9:'dp4',10:'min',11:'max',12:'slt',13:'sge',14:'exp',15:'log',18:'lrp',19:'frc',31:'dcl',32:'pow',33:'crs',34:'sgn',35:'abs',36:'nrm',37:'sincos',66:'texld',65:'texkill',88:'cmp',89:'dp2add',81:'def',82:'defi',83:'defb',79:'nop',90:'dsx',91:'dsy',95:'texldl',40:'if',42:'else',43:'endif',87:'setp',78:'lrp?',86:'cmp?'}
def reg(r,isdst=False):
    t=((r>>28)&7)|((r>>8)&0x18); n=r&0x7ff
    nm={0:'r',1:'v',2:'c',3:'s',4:'oPos' ,5:'?',6:'?',8:'oC',10:'oDepth'}.get(t,'t%d_'%t)
    return '%s%d'%(nm,n)
def dis(blob):
    n=len(blob)//4; t=struct.unpack_from('<%dI'%n,blob,0); i=1; out=[]
    while i<n:
        tok=t[i]; op=tok&0xffff
        if op==0xfffe: i+=1+((tok>>16)&0x7fff); continue
        if op==0xffff: break
        ln=(tok>>24)&0xf; pr=t[i+1:i+1+ln]
        if op in (81,): out.append('def c%d %s'%(pr[0]&0x7ff,struct.unpack('<4f',struct.pack('<4I',*pr[1:5])))) 
        elif op==31: out.append('dcl %s'%reg(pr[1]))
        else: out.append('%s %s'%(OPN.get(op,'op%d'%op),', '.join(reg(x) for x in pr)))
        i+=1+ln
    return out
if __name__=='__main__':
    lib=P[int(sys.argv[1])]
    print(lib.keys() if hasattr(lib,'keys') else type(lib)); print(len(lib['entries']), [hex(s) for s in lib['slots'][:20]])
    k=int(sys.argv[2])
    s=sorted(set(lib['slots'])-{0xFFFFFFFF})[k]
    print('slot',hex(s))
    for l in dis(lib['entries'][s]['blob']): print(l)
