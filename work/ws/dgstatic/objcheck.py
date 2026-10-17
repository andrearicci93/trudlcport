import sys, re, os, collections
sys.path.insert(0,'/path/to/trudlcport/tools'); sys.path.insert(0,'/path/to/trudlcport/work/ws/dgstatic')
import objlists as OL
from intros_cmp import *
log=open(W+'runs/du_B8_1/a1/engine.log',errors='replace').read()
loaded=[m.group(1).lower().replace('\\','/') for m in re.finditer(r'Loading PC-W\\([^\r\n]*?\.drm) from mods folder',log)]
loadedset=set(os.path.basename(x) for x in loaded)
pcpc=W+'baseline/B8/mods/'
have=set(f.lower() for f in os.listdir(pcpc))
pcobj={v.lower() for v in OL.read_objectlist(open(W+'generic/lists/pc_objectlist.txt','rb').read()).values()}
recs,first=OL.read_objlist(open(pcpc+'tr8/pc-w/objlist.dat','rb').read(),'le')
xrecs,_=OL.read_objlist(open(W+'dlc1/objlist.dat','rb').read(),'be')
rp=dict(recs); rx=dict(xrecs)
for u in ['dlc\\dlc_level1\\dlc_dungeon']:
    pass
for k,(n,l) in enumerate(recs):
    pass
def unitobjs(unit):
    for n,l in recs:
        if n.lower().endswith(unit): return [PO.get(i,'?%d'%i) for i in l]
def xunitobjs(unit):
    for n,l in xrecs:
        if n.lower().endswith(unit): return [XO.get(i,'?%d'%i) for i in l]
for unit in ['dlc_dungeon','dlc_dungeonhalla','dlc_dungeonhallb','dlc_treasureroom','dlc_watertunnel','dlc_pillory']:
    pu=unitobjs(unit); xu=xunitobjs(unit)
    print('=== objlist.dat',unit,'PC n=%d Xbox n=%d'%(len(pu),len(xu)),'  sets equal(by name):',set(pu)==set(xu))
    print('  onlyX',sorted(set(xu)-set(pu)),'onlyPC',sorted(set(pu)-set(xu)))
    for n in sorted(pu):
        f=n+'.drm'
        st='DRM in mods' if f in have else ('base PC object' if n in pcobj else 'NO DRM FILE')
        ld='LOADED' if f in loadedset else 'not-in-log'
        print('  %-42s %-16s %s'%(n,st,ld))
