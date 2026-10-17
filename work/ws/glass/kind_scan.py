"""Scan: texture entry bound to a sampler register whose declared dimension (dcl_cube/2d) differs from the texture (cube flag 0x8000).
Calibrated on PC base materials (textures from the PC bigfile)."""
import sys,os,struct,collections,json
sys.path.insert(0,'/path/to/trudlcport/tools')
from drm import cdrm_decode, sections_with_data
import drm_reloc as R, material_reslot as MR, tex_convert as T
L=MR.libs(); P=L['P']
def kinds_for(pt):
    plibs=[P.get(x) if x else None for x in pt[:3]]; k=collections.defaultdict(set)
    for i,lib in enumerate(plibs):
        if lib is None or lib['kind']!=1: continue
        for r,v in MR.sampler_kinds(lib,('k','p',pt[i])).items(): k[r]|=v
    return k
def mism(pd,pr,cube):
    pt=struct.unpack_from('<4I',pd,0x28); k=kinds_for(pt); out=[]
    for o,tid,ty,slot in MR.tex_entries(pd,R.parse(pr,'le'),'<'):
        if slot not in k or tid not in cube: continue
        want=k[slot]
        if len(want)==1:
            w=list(want)[0]; have='cube' if cube[tid] else '2d'
            if w!=have: out.append((slot,tid,ty,w,have))
    return out
if __name__=='__main__':
    root=sys.argv[1]; cube={}; mats={}
    for dp,dn,fn in os.walk(root):
        for f in sorted(fn):
            if not f.endswith('.drm'): continue
            p=os.path.join(dp,f)
            try: raw=cdrm_decode(open(p,'rb').read(),'le'); secs=sections_with_data(raw,'le')[1]
            except Exception: continue
            for s in secs:
                if s['type']==5: cube[s['id']]=bool(T.parse_pc(s['data'])['flags']&0x8000)
            for s in secs:
                if s['type']==10: mats[(os.path.relpath(p,root),s['id'])]=s
    n=0; rows=[]
    for (f,mid),s in mats.items():
        try: m=mism(s['data'],s['reloc'],cube)
        except Exception as e: continue
        if m: rows.append((f,mid,m))
    print('materials',len(mats),'textures',len(cube),'with kind mismatch',len(rows),'distinct mats',len({r[1] for r in rows}))
    for r in rows: print(r)
