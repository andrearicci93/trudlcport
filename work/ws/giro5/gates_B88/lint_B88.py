import sys, os, struct
sys.path.insert(0,'/path/to/trudlcport/work/ws/shader4'); sys.path.insert(0,'/path/to/trudlcport/work/ws/contratti')
import contract as C, f4_lint, glob
t=C.read_tree('/path/to/trudlcport/work/baseline/B88_fullpass/mods')
new=set(range(2775,2782)); n=w=0; seen=set(); tot_ins=0
for rel,d in t.items():
    for s in d.sections:
        if s.type==9 and s.id in new:
            f=C.frame_lib(s.data)
            assert not f['errors'], f['errors']
            for k,o in enumerate(f['slots']):
                if o==0xFFFFFFFF: continue
                bc=f['entries'][o]['bc']; key=(s.id,k)
                if key in seen: continue
                seen.add(key); n+=1
                errs=f4_lint.lint(bc, True)
                if errs: w+=1; print('WARN lib',s.id,'slot',k,errs[:3])
print('bytecode controllati (lib nuove 2756-2774, varianti uniche):',n,'| con warning:',w)
