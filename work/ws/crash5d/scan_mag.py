"""Famiglia: parola Xbox = intero piccolo (1..0xffff), PC >= 0x10000 e != bswap32 (convertita raw/b2s16/s16b2 invece di s32).
Scan DLC1 su un overlay (default baseline/B5/mods) + calibrazione sulle coppie base (stessa condizione, PC = verita')."""
import sys,os,struct,glob,json,collections
sys.path.insert(0,'/path/to/trudlcport/tools')
import dtp_audit as A, drm_reloc as R, drm_write as DW
W='/path/to/trudlcport/work/'
def cand(xd,pd,skip):
    out=[]
    for o in range(0,len(xd)-3,4):
        if o in skip: continue
        v=struct.unpack_from('>I',xd,o)[0]
        if not (1<=v<=0xffff): continue
        pv=struct.unpack_from('<I',pd,o)[0]
        if pv>=0x10000 and pv!=v:
            out.append((o,xd[o:o+4].hex(),pd[o:o+4].hex()))
    return out
def classof(xh,ph):
    x=bytes.fromhex(xh); p=bytes.fromhex(ph)
    return A.NAMES[[i for i,pp in enumerate(A.PERMS.values()) if bytes(x[j] for j in pp)==p][0]] if any(bytes(x[j] for j in pp)==p for pp in A.PERMS.values()) else 'other'
def base():
    n=0;hits=[];cnt=collections.Counter()
    for x,p,xb,pc,xr in A.base_pairs():
        xd,pd=xb['data'],pc['data']
        skip=set(xr.pointer_offsets())|set(xr.id_offsets())
        n+=len(xd)//4
        for o,xh,ph in cand(xd,pd,skip): hits.append((x,o,xh,ph)); cnt[classof(xh,ph)]+=1
    return n,hits,cnt
def scan(d):
    res=[]
    for p in sorted(glob.glob(d+'/**/*.drm',recursive=True)):
        rel=os.path.relpath(p,d).replace('\\','/')
        xs=A.xsecs(rel)
        if xs is None: continue
        D=DW.read(open(p,'rb').read(),'le')
        for x,i in A.section_pairs(xs,D):
            sec=D.sections[i]
            if x['type']!=7 or len(sec.data)!=len(x['data']) or A.base_content(x): continue
            xr=R.parse(x['reloc'],'be'); skip=set(xr.pointer_offsets())|set(xr.id_offsets())
            for o,xh,ph in cand(x['data'],sec.data,skip): res.append(dict(file=rel,id=sec.id,xid=x['id'],off=o,xbox=xh,pc=ph,cls=classof(xh,ph)))
    return res
if __name__=='__main__':
    d=sys.argv[1] if len(sys.argv)>1 else W+'baseline/B5/mods'
    n,h,c=base(); print('BASE words',n,'cand',len(h),dict(c))
    byc=collections.Counter((x,xh,ph) for x,o,xh,ph in h); print('base top',byc.most_common(8))
    r=scan(d); print('DLC cand',len(r),dict(collections.Counter(x['cls'] for x in r)))
    json.dump(dict(base=dict(words=n,cand=len(h),cls=dict(c)),dlc=r),open(W+'ws/crash5d/scan_mag.json','w'),indent=0)
    byf=collections.Counter((x['file'],x['id']) for x in r); print(len(byf),'DTPs',byf.most_common(30))
