"""derive byte-level field tables from base pairs for C (HS/HB/HC), TP, D(desc,node,trans) -> prints python literals"""
import sys; sys.path.insert(0,'/path/to/trudlcport/work/ws/schema')
from lib import *
from explore_c import elements, PERMS, cls
from explore_d import descs
import pickle, collections
pairs=pickle.load(open(T+'/work/generic/pairs.pkl','rb'))
NAMES=list(PERMS)
def collect():
    # (struct, off) -> list of (xw, pw, dtpkey)
    smp=collections.defaultdict(list)
    for name,((xh,xs),(ph,ps)) in pairs.items():
        if len(xs)!=len(ps): continue
        for s,p in zip(xs,ps):
            if s['type']!=7 or s['data'] is None or p['data'] is None or len(s['data'])!=len(p['data']): continue
            xd=s['data']; pd=p['data']; r=R.parse(s['reloc'],'be'); it=dict(r.internal)
            slots=set(r.pointer_offsets())|set(r.id_offsets()); key=(name,s['id'])
            def add(st,a,rel):
                if a in slots or a+4>len(xd): return
                smp[st,rel].append((xd[a:a+4],pd[a:a+4],key))
            for kind,e,es in elements(xd,r):
                for off in range(0,es,4): add(kind,e+off,off)
            for o in descs(xd,r):
                if xd[o:o+4]==bytes.fromhex('beebbeeb'): continue
                for off in range(0,0x54,4): add('DESC',o+off,off)
                n=struct.unpack_from('>I',xd,o+4)[0]; t1=it[o+8]
                for k in range(n):
                    nb=t1+28*k
                    for off in range(0,28,4): add('NODE',nb+off,off)
                    nt=struct.unpack_from('>I',xd,nb+0xc)[0]; tp=it.get(nb+0x10)
                    for q in range(nt):
                        tt=it.get(tp+4*q)
                        if tt is None: continue
                        for off in range(0,0x28,4): add('TRANS',tt+off,off)
    return smp
def derive(samples):
    inter=set(NAMES); n=0; dts=set(); exc=0; excs=[]
    for xw,pw,key in samples:
        c=cls(xw,pw)
        if len(c)==5: continue
        if not c: exc+=1; excs.append((xw.hex(),pw.hex(),key)); continue
        inter&=c; n+=1; dts.add(key)
    return inter,n,len(dts),exc,excs
def fields(inter):
    """determined byte groups from surviving perms"""
    perms=[PERMS[p] for p in sorted(inter)]
    if not perms: return None
    det={}
    for j in range(4):
        srcs={p[j] for p in perms}
        if len(srcs)==1: det[j]=srcs.pop()
    out=[]; j=0
    while j<4:
        if j not in det: out.append((j,1,'UNK')); j+=1; continue
        if j+3<4 and all(det.get(j+i)==3-i+j*0 for i in range(4)) and j==0: out.append((0,4,'u32')); j=4; continue
        if j+1<4 and det.get(j)==j+1 and det.get(j+1)==j: out.append((j,2,'u16')); j+=2; continue
        if det[j]==j: out.append((j,1,'u8')); j+=1; continue
        out.append((j,1,'UNK')); j+=1
    return out
if __name__=='__main__':
    smp=collect()
    for (st,off) in sorted(smp):
        inter,n,nd,exc,excs=derive(smp[st,off])
        print(st,hex(off),'n=%d dtp=%d exc=%d'%(n,nd,exc), sorted(inter), fields(inter) if n else None)
