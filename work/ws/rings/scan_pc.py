import sys,os
sys.path.insert(0,'/path/to/trudlcport/tools'); sys.path.insert(0,'/path/to/trudlcport/work/ws/rings')
import pairs as P, generic_cache as GC, scan_enable as SE
names=GC.names()
print(len(names),file=sys.stderr)
res={}
for i,nm in enumerate(names):
    try: t=P.pc_drm(nm)
    except Exception as ex: continue
    if not t: continue
    r=SE.scan(t[1])
    if r: print(nm,r,flush=True)
