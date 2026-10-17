import sys,json,collections; sys.path.insert(0,'/path/to/trudlcport/work/ws/crash5d')
import scan_sib as S
ns,h=S.base(); legit=set(a[2] for a in h)
r=json.load(open('/path/to/trudlcport/work/ws/crash5d/scan_sib.json'))['dlc']
print('base legit values',sorted(legit))
res=[x for x in r if x['xbox'] not in legit]
print(len(r),'->',len(res)); [print(x) for x in res]
