"""general check of ALL HInfo records (engine strides: g0 HS 0x24, g1 HB 0x50, g2 0x20, g3 HC 0x40, g4 0x70) of every model DTP in a set of DRMs:
Xbox bytes -> schema-declared PC bytes (field types alta/media only) vs installed PC bytes.  Also semantic: radius 0, flags without 0x100."""
import sys,struct,os,collections
sys.path.insert(0,'/path/to/trudlcport/work/ws/rigid')
import common as C
sys.path.insert(0,C.T); import dtp_schema as S
STRIDE={0:('HS',0x24),1:('HB',0x50),3:('HC',0x40)}
OTHER={2:0x20,4:0x70}
def run(base, files, out):
    tot=collections.Counter(); rows=[]
    for rel in files:
        D,xs,raw=C.load(rel,base)
        if xs is None: tot['noxbox']+=1; continue
        for x,i in C.A.section_pairs(xs,D):
            if x['type']!=7: continue
            sec=D.sections[i]
            if len(sec.data)!=len(x['data']) or x['data'][:4]!=C.MAGIC_X: continue
            xr=C.R.parse(x['reloc'],'be'); pr=C.R.parse(sec.reloc,'le'); it=dict(xr.internal)
            ns=C.u32(x['data'],4,'>'); seg=it.get(0xc)
            if seg is None or ns>300: continue
            xd=x['data']; pd=bytes(sec.data); slots=S._slots(xr)
            for j in range(ns):
                h=it.get(seg+0x40*j+0x3c)
                if h is None or h+0x28>len(xd): continue
                for k in range(5):
                    c=C.u32(xd,h+8*k,'>'); a=it.get(h+8*k+4)
                    if not c or a is None: continue
                    if k in STRIDE: kind,stride=STRIDE[k]
                    else: kind=None; stride=OTHER[k]
                    if a+stride*c>len(xd): rows.append((rel,sec.id,j,k,'OVERRUN',a,c)); continue
                    for q in range(c):
                        b=a+stride*q; tot['rec_g%d'%k]+=1
                        if kind is None:
                            continue
                        # semantic
                        if kind=='HS':
                            fl=struct.unpack_from('<H',pd,b)[0]; rad=struct.unpack_from('<H',pd,b+6)[0]
                            xfl=struct.unpack_from('>H',xd,b)[0]; xrad=struct.unpack_from('>H',xd,b+6)[0]
                            if rad==0: rows.append((rel,sec.id,j,k,'PC_RADIUS0 (xbox=%d)'%xrad,b,q))
                            if not (fl&0x100): rows.append((rel,sec.id,j,k,'PC_FLAGS_NO_0x100 fl=%04x (xbox %04x)'%(fl,xfl),b,q))
                        for f in S.SCHEMA[kind]:
                            if f.off+f.size>stride: continue
                            if f.type not in S.WRITABLE and f.type not in ('ptr','id(12)','key32','UNKNOWN_RAW'): continue
                            o=b+f.off
                            if any(t in slots for t in range(o-o%4,o+f.size)) or f.type in ('ptr','id(12)','key32','UNKNOWN_RAW'): continue
                            xb=xd[o:o+f.size]; exp=bytes(xb) if f.size==1 else bytes(reversed(xb))
                            pc=pd[o:o+f.size]
                            tot['fld_%s'%f.cert]+=1
                            if exp!=pc:
                                tot['MISMATCH_%s'%f.cert]+=1
                                rows.append((rel,sec.id,j,k,'FIELD %s.%s@%#x %s/%s xbox=%s pc=%s exp=%s'%(kind,f.name,o,f.type,f.cert,xb.hex(),pc.hex(),exp.hex()),b,q))
    with open(out,'w') as fh:
        fh.write('totals %s\n'%dict(tot))
        for r in rows: fh.write(' '.join(str(t) for t in r)+'\n')
    return tot,rows
if __name__=='__main__':
    base=sys.argv[1]; out=sys.argv[2]
    d=os.path.join(C.W,base)
    files=sorted(os.path.relpath(os.path.join(r,f),d) for r,_,fs in os.walk(d) for f in fs if f.endswith('.drm'))
    if len(sys.argv)>3: files=[f for f in files if any(p in f for p in sys.argv[3:])]
    t,r=run(base,files,out); print(dict(t),len(r))
