import sys,struct,collections,glob;sys.path.insert(0,'/path/to/trudlcport/work/ws/crash167');sys.path.insert(0,'/path/to/trudlcport/tools')
import fnd,dm,hashlib
D='/path/to/trudlcport/work/'
h,secs=fnd.load(D+'baseline/B6/mods/dlc_dungeon.drm')
d=[s for s in secs if s['i']==47][0]['data']
ranges=[]
for r in range(26):
    o=0xd4+0x40*r; w=struct.unpack_from('<I',d,o)[0]; ranges.append((w&0xffff,w>>16))
print(ranges)
T=(11593.5,-16927,11006)
N=105
ok=0;bad=[]
# estimate T from vertex 0..3 (k=1)
dv=lambda i:struct.unpack_from('<3f',d,0x720+16*i)
rv=lambda i:struct.unpack('<3f',dm.rd(0x207d8070+16*i,12))
T=tuple(a-b for a,b in zip(rv(0),dv(0)))
print('T',T)
for v in range(104):
    k=sum(1 for s,c in ranges if s<=v<s+c)
    exp=tuple(q+k*t for q,t in zip(dv(v),T)); r=rv(v)
    if all(abs(a-b)<=max(2.0,abs(b)*1e-5) for a,b in zip(r,exp)): ok+=1
    else: bad.append((v,k))
print('match',ok,'/104',bad[:10])
# B5 md5
for b in ('B1','B5','B6'):
    p=D+'baseline/%s/mods/dlc_dungeon.drm'%b
    try: print(b,hashlib.md5(open(p,'rb').read()).hexdigest())
    except Exception as e: print(b,e)
