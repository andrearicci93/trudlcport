import sys,glob
sys.path.insert(0,'/path/to/trudlcport/tools');sys.path.insert(0,'/path/to/trudlcport/work/ws/crash167')
import fnd, soundplex_fix as S
BASE='/path/to/trudlcport/work/baseline/B6/mods/'
for p in sorted(glob.glob(BASE+'**/*.drm',recursive=True)):
    rel=p.split('mods/')[1]
    try: xs=S.xsecs_of(rel)
    except Exception as e: print(rel,'xerr');continue
    if not xs: print(rel,'noxbox'); continue
    h,secs=fnd.load(p)
    if len(xs)!=len(secs): print(rel,'MISMATCH',len(xs),len(secs))
