"""Task 3.1: ogni lib nuova (2756-2774) e' usata da UN solo materiale in tutto l'albero B87, dallo stesso in tutti i DRM, con copie identiche; nessun altro materiale la referenzia."""
import sys, struct, collections, hashlib
sys.path.insert(0,'/path/to/trudlcport/work/ws/contratti')
import contract as C
t=C.read_tree('/path/to/trudlcport/work/baseline/B87_materiali19/mods')
use=collections.defaultdict(set); where=collections.defaultdict(set); copies=collections.defaultdict(set); mats_of=collections.defaultdict(set); lib_in=collections.defaultdict(set)
for rel,d in t.items():
    for s in d.sections:
        if s.type==10:
            lib=struct.unpack_from('<I',s.data,0x30)[0]; use[lib].add(s.id); where[lib].add(rel)
        if s.type==9: copies[s.id].add(hashlib.md5(s.data).hexdigest()); lib_in[s.id].add(rel)
new=list(range(2756,2775)); bad=0
for l in new:
    ok=len(use[l])==1 and len(copies[l])==1 and where[l]<=lib_in[l] and lib_in[l]<=where[l]
    bad+= not ok
    print('lib %d: materiali %s | DRM con materiale %d, DRM con lib %d, copie distinte %d -> %s'%(l,sorted(use[l]),len(where[l]),len(lib_in[l]),len(copies[l]),'OK' if ok else 'FAIL'))
mats=[m for l in new for m in use[l]]
print('materiali con lib dedicata:',len(mats),'distinti:',len(set(mats)),'| lib condivise o incoerenti:',bad)
