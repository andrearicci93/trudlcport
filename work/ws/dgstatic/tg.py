import sys, struct
sys.path.insert(0,'/path/to/trudlcport/tools'); sys.path.insert(0,'/path/to/trudlcport/work/ws/dgstatic')
from intros_cmp import *
for u in ['dlc_dungeon','dlc_watertunnel','dlc_treasureroom','dlc_dungeonhalla','dlc_dungeonhallb']:
    _,XL,xs=intros(W+'ws/dgstatic/xbox/%s.drm'%u,'be'); _,PL,ps=intros(W+'baseline/B8/mods/%s.drm'%u,'le')
    print('==',u,'tgs',len(XL['tgs']),len(PL['tgs']))
    for (xi,xo),(pi,po) in zip(XL['tgs'],PL['tgs']):
        xd=xs[xi]['data'][xo:xo+0x50]; pd=ps[pi]['data'][po:po+0x50]
        xw=struct.unpack('>20I',xd); pw=struct.unpack('<20I',pd)
        dif=[i for i in range(20) if xw[i]!=pw[i]]
        print('  tg uid %d/%d  words-differing %s'%(xw[10],pw[10],[(i*4,hex(xw[i]),hex(pw[i])) for i in dif][:6]))
