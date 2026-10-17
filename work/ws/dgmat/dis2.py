import sys,struct,re
sys.path.insert(0,'/path/to/trudlcport/work/ws/glass')
from ps_dis import OPN,reg,P
def src(t):
    sw=(t>>16)&0xff; s=''.join('xyzw'[(sw>>(2*i))&3] for i in range(4)); md=(t>>24)&0xf
    r=reg(t); 
    return ('-' if md==1 else '')+('1-' if md==2 else '')+r+('' if s=='xyzw' else '.'+s) + ('_abs' if md==11 else '')
def dst(t):
    m=(t>>16)&0xf; return reg(t)+'.'+''.join(c for i,c in enumerate('xyzw') if m>>i&1)+(('_sat' if (t>>20)&1 else ''))
def dis(blob):
    n=len(blob)//4; t=struct.unpack_from('<%dI'%n,blob,0); i=1; out=[]
    while i<n:
        tok=t[i]; op=tok&0xffff
        if op==0xfffe: i+=1+((tok>>16)&0x7fff); continue
        if op==0xffff: break
        ln=(tok>>24)&0xf; pr=t[i+1:i+1+ln]; nm=OPN.get(op,'op%d'%op)
        if op==81: out.append('def c%d'%(pr[0]&0x7ff)+str(struct.unpack('<4f',struct.pack('<4I',*pr[1:5]))))
        elif op==31: out.append('dcl '+reg(pr[1]))
        elif op in (40,42,43,79): out.append(nm+' '+', '.join(src(x) for x in pr))
        elif ln>=1: out.append(nm+' '+dst(pr[0])+', '+', '.join(src(x) for x in pr[1:]))
        else: out.append(nm)
        i+=1+ln
    return out
if __name__=='__main__':
    lib=P[int(sys.argv[1])]; sl=sorted(set(lib['slots'])-{0xFFFFFFFF}); s=sl[int(sys.argv[2])]
    ls=dis(lib['entries'][s]['blob']); a,b=int(sys.argv[3]),int(sys.argv[4])
    for i in range(a,min(b,len(ls))): print(i,ls[i])
