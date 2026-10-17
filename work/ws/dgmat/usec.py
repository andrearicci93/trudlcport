import sys,re
sys.path.insert(0,'/path/to/trudlcport/work/ws/glass')
from ps_dis import dis,P
lib=int(sys.argv[1]); regs=sys.argv[2].split(',')
L=P[lib]; sl=sorted(set(L['slots'])-{0xFFFFFFFF})
print('lib',lib,'perms',len(sl))
for s in sl[:int(sys.argv[3]) if len(sys.argv)>3 else 2]:
    ls=dis(L['entries'][s]['blob']); print('-- perm',hex(s),'ninstr',len(ls))
    for i,l in enumerate(ls):
        if any(re.search(r'\b%s\b'%r,l) for r in regs): print('%4d %s'%(i,l)); 
