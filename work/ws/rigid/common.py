import sys, os, struct
T='/path/to/trudlcport/tools'
sys.path.insert(0,T)
import drm_write as DW, drm_reloc as R, dtp_audit as A
W='/path/to/trudlcport/work'
def load(rel, base='baseline/B2/mods'):
    path=os.path.join(W,base,rel); raw=open(path,'rb').read(); D=DW.read(raw,'le')
    xs=A.xsecs(rel)
    return D,xs,raw

MAGIC_X=bytes.fromhex('04c20453')
def u32(d,o,e): return struct.unpack_from(e+'I',d,o)[0]
def model_info(d, rel, e):
    """HInfo group counts per segment. returns None if not a model DTP"""
    it=dict(rel.internal)
    if len(d)<0x80: return None
    ns=u32(d,4,e); seg=it.get(0xc)
    if seg is None or ns>200 or seg+0x40*ns>len(d): return None
    out=[]
    for j in range(ns):
        b=seg+0x40*j
        h=it.get(b+0x3c)
        fl=d[b+0x30]
        if h is None or h+0x28>len(d): out.append((j,fl,None)); continue
        cnt=[u32(d,h+8*k,e) for k in range(5)]
        ptrs=[it.get(h+8*k+4) for k in range(5)]
        out.append((j,fl,cnt,ptrs))
    return out
