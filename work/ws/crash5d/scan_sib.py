"""Rilevatore 'fratello': parola Xbox intero piccolo (1..0xff, shape B3) convertita NON s32 (PC != v) mentre un record
gemello nello stesso DTP (stesso contesto di 4 parole attorno) ha la stessa parola convertita s32.  Calibrazione: coppie base (PC vero)."""
import sys,os,struct,glob,json,collections
sys.path.insert(0,'/path/to/trudlcport/tools'); sys.path.insert(0,'/path/to/trudlcport/work/ws/crash5d')
import dtp_audit as A, drm_reloc as R, drm_write as DW
W='/path/to/trudlcport/work/'
MAXV=0xff
def det(xd,pd,skip):
    n=len(xd)//4
    X=struct.unpack('>%dI'%n,xd[:n*4]); P=struct.unpack('<%dI'%n,pd[:n*4])
    S=set(o//4 for o in skip)
    idx=collections.defaultdict(list)
    for i in range(2,n-2):
        if 1<=X[i]<=MAXV and i not in S: idx[(X[i-2],X[i-1],X[i+1],X[i+2])].append(i)
    out=[]
    for k,l in idx.items():
        if len(l)<2: continue
        good=[i for i in l if P[i]==X[i]]; bad=[i for i in l if P[i]!=X[i]]
        if good and bad:
            for i in bad: out.append((i*4,xd[i*4:i*4+4].hex(),pd[i*4:i*4+4].hex(),len(good),len(bad)))
    return out
def base():
    hits=[];nsec=0
    for x,p,xb,pc,xr in A.base_pairs():
        skip=set(xr.pointer_offsets())|set(xr.id_offsets())
        r=det(xb['data'],pc['data'],skip); nsec+=1
        for t in r: hits.append((x,)+t)
    return nsec,hits
def scan(d):
    res=[]
    for p in sorted(glob.glob(d+'/**/*.drm',recursive=True)):
        rel=os.path.relpath(p,d).replace('\\','/'); xs=A.xsecs(rel)
        if xs is None: continue
        D=DW.read(open(p,'rb').read(),'le')
        for x,i in A.section_pairs(xs,D):
            sec=D.sections[i]
            if x['type']!=7 or len(sec.data)!=len(x['data']) or A.base_content(x): continue
            xr=R.parse(x['reloc'],'be'); skip=set(xr.pointer_offsets())|set(xr.id_offsets())
            for o,xh,ph,g,b in det(x['data'],sec.data,skip): res.append(dict(file=rel,id=sec.id,xid=x['id'],off=o,xbox=xh,pc=ph,sib_s32=g,sib_other=b))
    return res
if __name__=='__main__':
    d=sys.argv[1] if len(sys.argv)>1 else W+'baseline/B5/mods'
    ns,h=base(); print('BASE sections',ns,'flagged words',len(h),'distinct DTP',len(set(x[0] for x in h)))
    print(collections.Counter((a[3],a[4]) for a in h).most_common(8))
    r=scan(d); print('DLC flagged',len(r)); 
    for x in r[:60]: print(x)
    json.dump(dict(base_flagged=len(h),dlc=r),open(W+'ws/crash5d/scan_sib.json','w'),indent=0)
