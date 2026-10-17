import sys,struct;sys.path.insert(0,'/path/to/trudlcport/work/ws/crash167')
import fnd,dm
h,secs=fnd.load('/path/to/trudlcport/work/baseline/B6/mods/dlc_dungeon.drm')
d=[s for s in secs if s['i']==47][0]['data']
for pi in [0,1,4,5,8,12,20,24,40,60,72,76,80,84,88,92,96,100,101]:
    dv=struct.unpack_from('<3f',d,0x720+16*pi)
    rv=struct.unpack('<3f',dm.rd(0x207d8070+16*pi,12))
    print(pi,['%.0f'%x for x in dv],['%.0f'%x for x in rv],['%.0f'%(r-q) for r,q in zip(rv,dv)])
