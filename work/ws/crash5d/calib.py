import sys,collections; sys.path.insert(0,'/path/to/trudlcport/work/ws/crash5d')
import scan_sib as S
ns,h=S.base()
c=collections.Counter(a[2] for a in h); print(c.most_common(30))
cd=collections.Counter(a[2] for a in h if a[2]!='00000001'); print('non-1',sum(cd.values()),len(set(a[0] for a in h if a[2]!='00000001')))
# for value e0 in base: contexts
for a in h:
    if a[2] in ('000000e0','000000ce','000000dd'): print(a)
