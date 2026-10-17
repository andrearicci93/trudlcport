import sys,struct
sys.path.insert(0,'/path/to/trudlcport/tools');sys.path.insert(0,'/path/to/trudlcport/work/ws/crash167')
import fnd, soundplex_fix as S, scan2
xs=S.xsecs_of('dlc_dungeon.drm'); h,secs=fnd.load(scan2.BASE+'dlc_dungeon.drm')
xd=xs[67]['data'];pd=secs[67]['data']
for o in range(0xa0,0x1c0,0x40):
    print(hex(o),'X',' '.join('%08x'%x for x in struct.unpack_from('>16I',xd,o)))
    print(hex(o),'P',' '.join('%08x'%x for x in struct.unpack_from('<16I',pd,o)))
