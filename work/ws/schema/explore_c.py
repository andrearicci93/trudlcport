import sys; sys.path.insert(0,'/path/to/trudlcport/work/ws/schema')
from lib import *
import pickle, collections
PERMS = {'s32': (3, 2, 1, 0), 's16': (1, 0, 3, 2), 'raw': (0, 1, 2, 3), 'b2s16': (0, 1, 3, 2), 's16b2': (1, 0, 2, 3)}
def cls(xw,pw): return frozenset(n for n,p in PERMS.items() if bytes(xw[j] for j in p)==pw)
MAGIC=bytes.fromhex('04c20453'); HSIZE={0:('HS',36),1:('HB',68),3:('HC',56)}
def elements(xd, rel):
    if xd[:4]!=MAGIC or len(xd)<0x80: return
    it=dict(rel.internal); tg=sorted(set(it.values())|{len(xd)})
    def nxt(a): return min([v for v in tg if v>a],default=len(xd))
    n=struct.unpack_from('>I',xd,0x5c)[0]; a=it.get(0x60)
    if n and a is not None and nxt(a)-a==32*n and a+32*n<=len(xd):
        for q in range(n): yield 'TP',a+32*q,32
    seg=it.get(0xc); ns=struct.unpack_from('>I',xd,4)[0]
    if seg is None or seg+0x40*ns>len(xd): return
    for j in range(ns):
        h=it.get(seg+0x40*j+0x3c)
        if h is None or h+0x28>len(xd): continue
        for k,(kind,es) in HSIZE.items():
            c=struct.unpack_from('>I',xd,h+8*k)[0]; a=it.get(h+8*k+4)
            if not c or a is None or nxt(a)-a!=es*c: continue
            for q in range(c): yield kind,a+es*q,es
if __name__=='__main__':
    pairs=pickle.load(open(T+'/work/generic/pairs.pkl','rb'))
    st=collections.defaultdict(collections.Counter); dt=collections.defaultdict(set); ex=collections.defaultdict(collections.Counter)
    for name,((xh,xs),(ph,ps)) in pairs.items():
        if len(xs)!=len(ps): continue
        for s,p in zip(xs,ps):
            if s['type']!=7 or s['data'] is None or p['data'] is None or len(s['data'])!=len(p['data']): continue
            xd=s['data']; pd=p['data']; r=R.parse(s['reloc'],'be')
            slots=set(r.pointer_offsets())|set(r.id_offsets())
            for kind,e,es in elements(xd,r):
                for off in range(0,es,4):
                    a=e+off
                    if a in slots: continue
                    c=cls(xd[a:a+4],pd[a:a+4]); key=tuple(sorted(c)) if len(c)<5 else 'ALL'
                    st[kind,off][key]+=1; dt[kind,off].add((name,s['id']))
    for k in sorted(st): print(k, dict(st[k]), 'dtps',len(dt[k]))
