import sys, os, struct, hashlib, collections
sys.path.insert(0,'tools')
import drm_write as DW, drm_reloc as R, tex_convert as TC, material_reslot as MR
ROOT='work/baseline/B8/mods'
WT={6610,6611,6612,6613,6752,6753,6754,6743,6744,6745}
res=[]
for dp,dn,fn in os.walk(ROOT):
    for f in sorted(fn):
        if not f.endswith('.drm'): continue
        p=os.path.join(dp,f); rel=os.path.relpath(p,ROOT)
        try:
            raw=DW.cdrm_decode(open(p,'rb').read(),'le'); D=DW.read(raw,'le')
        except Exception as e:
            print('ERR',rel,e); continue
        for s in D.sections:
            if s.type==5 and s.id in WT:
                try: h,k,r=TC.pc_levels(s.data); kind=k
                except Exception as e: kind='?'+str(e)[:20]
                print('TEX',rel,s.id,kind,len(s.data),hashlib.md5(s.data).hexdigest()[:10])
            if s.type==10:
                try:
                    rl=R.parse(s.reloc,'le')
                    te=[(t,ty) for o,t,ty,sl in MR.tex_entries(s.data,rl,'<')]
                except Exception as e: continue
                ids={t for t,_ in te}
                if ids&WT:
                    tup=struct.unpack_from('<4I',s.data,0x28)
                    print('MAT',rel,s.id,tup,sorted(ids&WT),hashlib.md5(s.data).hexdigest()[:10])
