import sys,struct;sys.path.insert(0,'/path/to/trudlcport/work/ws/crash167')
import fnd
P=sys.argv[1] if len(sys.argv)>1 else '/path/to/trudlcport/work/baseline/B6/mods/dlc_dungeon.drm'
h,secs=fnd.load(P)
for s in secs:
    d=s['data']; 
    if s['type']!=0: continue
    n=d.count(b'\xeb\xbe\xeb\xbe')
    if n: print('sec',s['i'],len(d),'magic count',n)
