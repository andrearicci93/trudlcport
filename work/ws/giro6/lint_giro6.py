"""Giro 6: lint lib nuove (2782 = lib dedicata mat 20323; 975/976 copiate negli streamgroup dungeon) + copie identiche in ogni DRM."""
import sys, hashlib
sys.path.insert(0,'/path/to/trudlcport/work/ws/shader4'); sys.path.insert(0,'/path/to/trudlcport/work/ws/contratti')
import contract as C, f4_lint
t=C.read_tree('/path/to/trudlcport/work/ws/giro6/compose/mods')
new={2782,975,976}; n=w=0; seen=set(); md5={}
for rel,d in t.items():
    for s in d.sections:
        if s.type==9 and s.id in new:
            md5.setdefault(s.id,{})[rel]=hashlib.md5(s.data).hexdigest()
            f=C.frame_lib(s.data); assert not f['errors'], f['errors']
            for k,o in enumerate(f['slots']):
                if o==0xFFFFFFFF: continue
                bc=f['entries'][o]['bc']; key=(s.id,k,hashlib.md5(bc).hexdigest())
                if key in seen: continue
                seen.add(key)
                if bc[:2]!=b'\x00\x03' or bc[2:4]!=b'\xff\xff': pass
                try: errs=f4_lint.lint(bc, True)
                except Exception as e: errs=['eccezione %r'%e]; 
                n+=1
                if errs: w+=1; print('WARN lib',s.id,'slot',k,errs[:3])
for lid,m in sorted(md5.items()): print('lib',lid,'copie',len(m),'md5 distinti',len(set(m.values())))
print('varianti controllate',n,'con warning',w)
