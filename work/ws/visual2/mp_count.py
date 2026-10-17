"""mp_count.py - conteggio MaterialParams (0x58) vs registri MaterialParams dichiarati dalle lib PC (VS+PS, tutti i passi).
Selftest: materiali base PC (count < dichiarato). Poi materiali DLC in B33/mods."""
import sys,struct,collections,os
sys.path.insert(0,'/path/to/trudlcport/tools')
import material_reslot as MR, drm_write as DW, dtp_audit as DA
from shaderlib import constants
L=MR.libs(); P=L['P']; PM=L['PM']
_c={}
def decl(sid):
    """max registro MaterialParams relativo (ri+rc-100) dichiarato dalla lib, e quale"""
    if sid in _c: return _c[sid]
    lib=P.get(sid); res=0
    if lib:
        for s in set(lib['slots'])-{0xFFFFFFFF}:
            v,c=constants(lib['entries'][s]['blob'],'p' )
            for n,rs,ri,rc in c:
                if n=='MaterialParams': res=max(res,ri+rc-100)
    _c[sid]=res; return res
def need(d):
    t=struct.unpack_from('<4I',d,0x28)
    return max([decl(s) for s in t if s] or [0])
def cnt(d): return struct.unpack_from('<I',d,0x58)[0]
if __name__=='__main__':
    c=collections.Counter(); ex=[]
    for k,(d,r) in PM.items():
        n,m=cnt(d),need(d); c['short' if n<m else 'ok' if n==m else 'longer']+=1
        if n<m: ex.append((k,n,m))
    print('BASE PC',dict(c),ex[:10])
    rows=[]
    for rel,path in sorted(DA.overlay(['baseline/B33/mods'],None).items()):
        try: D=DW.read(open(path,'rb').read(),'le')
        except Exception: continue
        for s in D.sections:
            if s.type==10 and len(s.data)>=0x60:
                n,m=cnt(s.data),need(s.data); rows.append((rel,s.id,n,m,struct.unpack_from('<4I',s.data,0x28)))
    seen={}
    for r in rows: seen[(r[1],r[2],r[3])]=r
    cc=collections.Counter('short' if r[2]<r[3] else 'ok' if r[2]==r[3] else 'longer' for r in seen.values())
    print('DLC materiali distinti (id,count,need)',len(seen),dict(cc))
    sh=[r for r in seen.values() if r[2]<r[3]]
    for r in sorted(sh,key=lambda r:r[1])[:60]: print(r[1],'count',r[2],'need',r[3],r[4],r[0])
    open('/path/to/trudlcport/work/ws/visual2/mp_count_short.tsv','w').write('\n'.join('%d\t%d\t%d\t%s\t%s'%(r[1],r[2],r[3],r[4],r[0]) for r in sh))
