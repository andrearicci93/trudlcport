import sys, io, contextlib, struct
sys.path.insert(0,'/path/to/trudlcport/work/ws/giro5')
with contextlib.redirect_stdout(io.StringIO()):
    import build_unlit as B
C=B.F14.C; DM=B.libs()['DM']
tree=C.read_tree(sys.argv[1])
for mid in map(int,sys.argv[2:]):
    xd=DM[mid][0]
    print('mat',mid,'XBOX', xd[0x28:0x74].hex(' ',4) if False else ' '.join(xd[o:o+4].hex() for o in range(0x28,0x74,4)))
    for rel,d in tree.items():
        for s in d.sections:
            if s.type==10 and s.id==mid:
                print('  PC ',rel.split('/')[-1][:26].ljust(26), ' '.join(s.data[o:o+4].hex() for o in range(0x28,0x74,4))); break
