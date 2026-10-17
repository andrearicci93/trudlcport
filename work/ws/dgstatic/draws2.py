import sys, os, struct, collections
sys.path.insert(0,'/path/to/trudlcport/tools')
import drm, drm_reloc as R
W='/path/to/trudlcport/work/'
def secs(p,e):
    raw=drm.cdrm_decode(open(p,'rb').read(),e); return drm.sections_with_data(raw,e)[1]
def lists(s,e):
    E='>' if e=='be' else '<'; out=[]
    for i,x in enumerate(s):
        if x['type']!=7: continue
        d=x['data']; n=len(d)
        k=struct.unpack_from(E+'I',d,0)[0] if n>=4 else 0
        if k==0 or n!=4+16*k: out.append(None); continue
        out.append((x['id'],k,tuple(struct.unpack_from(E+'I',d,4+16*j+12)[0] for j in range(k)),tuple(struct.unpack_from(E+'I',d,4+16*j+8)[0] for j in range(k)),tuple(struct.unpack_from(E+'I',d,4+16*j+4)[0] for j in range(k))))
    return out
P=W+'baseline/B8/mods/streamgroups/'; X=W+'ws/dgstatic/xbox/'
T=collections.Counter()
for f in sorted(os.listdir(P)):
    if not f.startswith(('dlc_dungeon','dlc_treasure','dlc_watertunnel')): continue
    xl=lists(secs(X+f,'be'),'be'); pl=lists(secs(P+f,'le'),'le')
    nl=sum(1 for v in xl if v); nd=sum(v[1] for v in xl if v); pd=sum(v[1] for v in pl if v)
    mis=[(a,b) for a,b in zip(xl,pl) if (a is None)!=(b is None) or (a and (a[1]!=b[1] or a[2]!=b[2]))]
    idmis=sum(1 for a,b in zip(xl,pl) if a and b and a[0]!=b[0])
    one_x=collections.Counter(v for a in xl if a for v in a[3]); one_p=collections.Counter(v for a in pl if a for v in a[3])
    print('%-55s t7 %d/%d  draw-lists X %d PC %d, draws X %d PC %d, list/matIdx mismatches %d, id!= %d, "one" X %s PC %s'%(f,len(xl),len(pl),nl,sum(1 for v in pl if v),nd,pd,len(mis),idmis,dict(one_x),dict(one_p)))
    for a,b in mis[:3]: print('    X',a,'\n    P',b)
