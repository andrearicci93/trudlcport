import sys,struct,os,collections
sys.path.insert(0,'/path/to/trudlcport/work/ws/rigid')
import common as C
sys.path.insert(0,C.T)
import dtp_schema as S
def model_status(d, rel, e, byid, sec_getter):
    pass
class _I: pass
def desc_by_header(d, rel):
    '''DESC array from the object header: X=internal[0xc0]; n=u32[X+8]; P=internal[X+0xc]; stride 0x54'''
    it=dict(rel.internal)
    if len(d)<0x140 or 0xc0 not in it: return []
    X=it[0xc0]
    if X+0x10>len(d) or (X+0xc) not in it: return []
    n=C.u32(d,X+8,'>'); P=it[X+0xc]
    if not 0<n<=64 or P+0x54*n>len(d): return []
    out=[]
    for k in range(n):
        i=_I(); i.base=P+0x54*k; out.append(i)
    return out
def analyze(rel, base='baseline/B2/mods', verbose=True):
    D,xs,raw=C.load(rel, base)
    if xs is None: return None
    prs=A=C.A.section_pairs(xs,D)
    pcs={(s.type,s.id):s for s in D.sections}
    xbs={(x['type'],x['id']):x for x in xs}
    res=[]
    for x,i in prs:
        if x['type']!=7: continue
        sec=D.sections[i]
        if len(sec.data)!=len(x['data']): continue
        xr=C.R.parse(x['reloc'],'be'); pr=C.R.parse(sec.reloc,'le')
        dd={i.base:i for i in desc_by_header(x['data'],xr)}
        for i in S.find_D(x['data'],xr):
            if i.struct=='DESC': dd.setdefault(i.base,i)
        descs=[dd[k] for k in sorted(dd)]
        if not descs: continue
        # model id run (PC ids & Xbox ids by same slot)
        pids=[(o,struct.unpack_from('<I',sec.data,o)[0]) for o in sorted(pr.id_offsets())]
        xids=[(o,struct.unpack_from('>I',x['data'],o)[0]) for o in sorted(xr.id_offsets())]
        def models(ids, getter, e):
            out=[]
            for o,i2 in ids:
                t=getter(i2)
                if t is None: continue
                dd,rr=t
                if dd[:4] in (C.MAGIC_X, C.MAGIC_X[::-1]) and len(dd)>=0x80:
                    out.append((o,i2,C.model_info(dd,rr,e)))
            return out
        def pget(i2):
            s=pcs.get((7,i2)); return None if s is None or s.data is None else (s.data,C.R.parse(s.reloc,'le'))
        def xget(i2):
            s=xbs.get((7,i2))
            if s is None:
                return None
            return (s['data'],C.R.parse(s['reloc'],'be'))
        pm=models(pids,pget,'<'); xm=models(xids,xget,'>')
        for ins in descs:
            b=ins.base
            pd=sec.data; xd=x['data']
            res.append(dict(file=rel,pc_id=sec.id,xid=x['id'],desc=b,
              p_flag=pd[b+0x2c], x_flag=xd[b+0x2c], p_midx=pd[b+0x18], x_midx=xd[b+0x18],
              p_arg=pd[b+0x1c:b+0x20].hex(), x_arg=xd[b+0x1c:b+0x20].hex(),
              pm=pm, xm=xm))
    return res
def usable(mi):
    """would the list for this model contain type 1/5/0xa/0xd records?  mi from model_info"""
    if mi is None: return False,'no segments/not model'
    n=0; why=[]
    for m in mi:
        j,fl,cnt=m[0],m[1],m[2]
        if cnt is None: why.append('seg%d nohdr'%j); continue
        if fl&8: why.append('seg%d flag8'%j); continue
        n+=cnt[0]+cnt[1]+cnt[3]+cnt[4]
    return n>0,'rec(1,5,a,d)=%d %s'%(n,' '.join(why))
if __name__=='__main__':
    base=sys.argv[1] if len(sys.argv)>1 else 'baseline/B2/mods'
    files=sys.argv[2:] or sorted(f for f in os.listdir(os.path.join(C.W,base)) if f.endswith('.drm') and ('dlc' in f.lower()))
    for f in files:
        try: r=analyze(f,base)
        except Exception as ex:
            print(f,'ERR',repr(ex)); continue
        if not r: continue
        for d in r:
            pm=d['pm']; xm=d['xm']
            pu=usable(pm[d['p_midx']][2]) if d['p_midx']<len(pm) else (False,'idx out of range (%d models)'%len(pm))
            xu=usable(xm[d['x_midx']][2]) if d['x_midx']<len(xm) else (False,'idx out of range (%d models)'%len(xm))
            flag='RIGID' if d['p_flag']&1 else '-'
            bad = (d['p_flag']&1) and not pu[0]
            print('%s%-34s dtp%-6d desc@%#x  flagPC=%02x flagXB=%02x midxPC=%d midxXB=%d nmod=%d/%d  PCusable=%s (%s) XBusable=%s (%s)'%('!! ' if bad else '   ',f,d['pc_id'],d['desc'],d['p_flag'],d['x_flag'],d['p_midx'],d['x_midx'],len(pm),len(xm),pu[0],pu[1],xu[0],xu[1]))
