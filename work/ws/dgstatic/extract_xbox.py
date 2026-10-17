import sys, re
sys.path.insert(0,'/path/to/trudlcport/tools')
from archive import Archive
import dlc_names as D
names={}
for l in open('/path/to/trudlcport/work/generic/dlc_names.txt'):
    p=l.split(None,5)
    if len(p)==6: names[int(p[0],16)]=p[5].strip()
want=re.compile(r'(dlc_(dungeon|treasureroom|watertunnel|pillory)|dlc1_(uo|ei|pt)_|dlc1_health|dlc_dispatcher|knight_thrall|co_dlc|streamgroups.dlc_(dungeon|treasure|watertunnel|pillory))')
A=Archive(D.PACKS['pack10'],'be')
import os
n=0
for r in A.idx:
    nm=names.get(r['hash'])
    if not nm or not nm.endswith('.drm'): continue
    if want.search(nm):
        out='xbox/'+nm.split('\\')[-1]
        if os.path.exists(out): continue
        open(out,'wb').write(A.read(r)); n+=1
print(n)
