import sys,collections,os
sys.path.insert(0,'.')
import mat_hdr as M
for f in sys.argv[1:]:
    for sid,c0,c1,c2,es in M.mats(f):
        has4=[i for i,(ty,sl) in enumerate(es) if ty==4]
        # misplaced: ty4 entry index >= c2 (in group C)
        bad=[i for i in has4 if i>=c2]
        if bad: print(os.path.basename(f),sid,'c50',c0,'c51',c1,'c52',c2,'ty4 idx',bad,[t for t,_ in es])
