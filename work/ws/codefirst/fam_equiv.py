"""Per ognuna delle 6 famiglie: coppie base (xs',pd') con blocco luci Xbox equivalente a quello di xs (find_donors) e materiali ponte disponibili."""
import sys,collections
S4='/path/to/trudlcport/work/ws/shader4'; sys.path.insert(0,S4)
from f9_transplant import *
fams=[(1431,1060),(981,1531),(111,225),(164,207),(1409,1038),(300,356)]
rev=collections.defaultdict(list)
for x,p in x2p().items(): rev[p].append(x)
for xs,pd in fams:
    print('=== (%d,%d) xs->pd gemelli di pd: %s'%(xs,pd,rev[pd]))
    tot=0
    for x in rev[pd]:
        br=material_pairs(x,pd); tot+=len(br); print('   Xbox %d / PC %d: %d materiali ponte'%(x,pd,len(br)))
    d=find_donors('X',xs,0,want=40)
    print('   find_donors(X,%d): %s'%(xs,d))
    for (x2,p2) in d:
        print('      equiv (%d,%d): materiali ponte %d'%(x2,p2,len(material_pairs(x2,p2))))
