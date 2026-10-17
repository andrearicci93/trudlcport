import sys, collections, struct, math
sys.path.insert(0,'tools')
import dtp_audit as A, drm_reloc as R
def plaus(v, lo=1e-4, hi=1e6):
    return math.isfinite(v) and lo<=abs(v)<=hi
cnt=collections.Counter(); ex=collections.defaultdict(list)
for x,p,xb,pc,xr in A.base_pairs():
    xd=xb['data']; pd=pc['data']; slots=set(xr.pointer_offsets())|set(xr.id_offsets())
    spans=A.string_spans(xd,xr)
    strw=set()
    for a,z,k in spans:
        for q in range(a-a%4,z+1,4): strw.add(q)
    for o in range(0,len(xd)-3,4):
        if o in slots or o in strw: continue
        xw=xd[o:o+4]; pw=pd[o:o+4]
        fx=struct.unpack('>f',xw)[0]; fp=struct.unpack('<f',pw)[0]
        if not plaus(fx): continue
        c=A.cls(xw,pw)
        s32=bool(c&1)
        pl=plaus(fp)
        key=('s32' if s32 else 'notS32', 'pcPlaus' if pl else 'pcImplaus')
        cnt[key]+=1
        if not s32 and not pl and len(ex[key])<15: ex[key].append((x,hex(o),xw.hex(),pw.hex()))
print(cnt)
for k,v in ex.items(): print(k,v)
