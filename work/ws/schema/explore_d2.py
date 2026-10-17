import sys; sys.path.insert(0,'/path/to/trudlcport/work/ws/schema')
from explore_d import *
PERMS = {'s32': (3, 2, 1, 0), 's16': (1, 0, 3, 2), 'raw': (0, 1, 2, 3), 'b2s16': (0, 1, 3, 2), 's16b2': (1, 0, 2, 3)}
def cls(xw,pw): return frozenset(n for n,p in PERMS.items() if bytes(xw[j] for j in p)==pw)
pairs=pickle.load(open(T+'/work/generic/pairs.pkl','rb'))
st=collections.defaultdict(lambda: collections.defaultdict(collections.Counter)); dt=collections.defaultdict(lambda: collections.defaultdict(set))
vals=collections.defaultdict(collections.Counter)
for name,((xh,xs),(ph,ps)) in pairs.items():
    if len(xs)!=len(ps): continue
    for s,p in zip(xs,ps):
        if s['type']!=7 or s['data'] is None or p['data'] is None or len(s['data'])!=len(p['data']): continue
        xd=s['data']; pd=p['data']; r=R.parse(s['reloc'],'be'); it=dict(r.internal)
        slots=set(r.pointer_offsets())|set(r.id_offsets())
        for o in descs(xd,r):
            for off in range(0,0x54,4):
                a=o+off
                if a in slots: continue
                c=cls(xd[a:a+4],pd[a:a+4])
                key=tuple(sorted(c)) if len(c)<5 else 'ALL'
                st['desc'][off][key]+=1; dt['desc'][off].add((name,s['id']))
                if len(c)<5: vals[('desc',off)][xd[a:a+4].hex()]+=1
            n=struct.unpack_from('>I',xd,o+4)[0]; t1=it[o+8]
            for k in range(n):
                nb=t1+28*k
                for off in range(0,28,4):
                    a=nb+off
                    if a in slots or a+4>len(xd): continue
                    c=cls(xd[a:a+4],pd[a:a+4]); key=tuple(sorted(c)) if len(c)<5 else 'ALL'
                    st['node'][off][key]+=1; dt['node'][off].add((name,s['id']))
                    if len(c)<5: vals[('node',off)][xd[a:a+4].hex()]+=1
                nt=struct.unpack_from('>I',xd,nb+0xc)[0]; tp=it.get(nb+0x10)
                if tp is None: continue
                for q in range(min(nt,32)):
                    tt=it.get(tp+4*q)
                    if tt is None: continue
                    for off in range(0,0x28,4):
                        a=tt+off
                        if a in slots or a+4>len(xd): continue
                        c=cls(xd[a:a+4],pd[a:a+4]); key=tuple(sorted(c)) if len(c)<5 else 'ALL'
                        st['trans'][off][key]+=1; dt['trans'][off].add((name,s['id']))
                        if len(c)<5: vals[('trans',off)][xd[a:a+4].hex()]+=1
for S in st:
    print('==',S)
    for off in sorted(st[S]):
        print(hex(off), dict(st[S][off]), 'dtps',len(dt[S][off]), list(vals[(S,off)].most_common(4)))
print('---- +0x50 s32 cases')
for name,((xh,xs),(ph,ps)) in pairs.items():
    if len(xs)!=len(ps): continue
    for s,p in zip(xs,ps):
        if s['type']!=7 or s['data'] is None or p['data'] is None or len(s['data'])!=len(p['data']): continue
        xd=s['data']; pd=p['data']; r=R.parse(s['reloc'],'be')
        for o in descs(xd,r):
            a=o+0x50
            c=cls(xd[a:a+4],pd[a:a+4])
            if c==frozenset({'s32'}): print(name,s['id'],hex(o),len(xd),xd[o:o+0x54].hex())
