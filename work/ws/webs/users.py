import sys,os,struct
sys.path.insert(0,'tools')
import drm_write as DW, drm_reloc as R
ROOT='work/baseline/B8/mods'
T={(10,20264),(10,23173),(10,20876),(10,20265),(10,20676),(10,20673),(10,23329)}
for dp,dn,fn in os.walk(ROOT):
  for f in sorted(fn):
    if not f.endswith('.drm'): continue
    p=os.path.join(dp,f); rel=os.path.relpath(p,ROOT)
    if not any(k in rel for k in ('dungeon','pillory','treasure','watertunnel','water_wheel','caverns')): continue
    D=DW.read(DW.cdrm_decode(open(p,'rb').read(),'le'),'le')
    for s in D.sections:
        if s.type==10 or not s.reloc: continue
        rl=R.parse(s.reloc,'le')
        offs=[(o,t) for t,o in rl.idref+rl.idref_a]
        hit=set()
        for t,o in rl.idref:
            if o//1>=0 and o+4<=len(s.data):
                v=struct.unpack_from('<I',s.data,o)[0]
                if (t,v) in T: hit.add(v)
        if hit: print(rel,'sec',s.type,s.id,len(s.data),sorted(hit))
