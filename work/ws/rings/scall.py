import sys,struct
sys.path.insert(0,'/path/to/trudlcport/work/ws/rings')
from sdump import *
def index(path,e='le'):
    secs=load(path,e); info={}
    for s in secs:
        if s['type']!=8 or s['size']<0x50: continue
        d=s['data']; rel=R.parse(s['reloc'],e); it=dict(rel.internal)
        try: W=SC.Walk(d,rel,e).run()
        except Exception: continue
        nn=cstr(d,it[0x10]) if 0x10 in it else None
        info[s['i']]=(s,W,nn)
    return secs,info
def resolve(info,si,off):
    if si not in info: return None
    s,W,nn=info[si]
    for name,t,n,sz in W.arrays:
        if name in ('protos','funcs','members') and t<=off<t+n*sz:
            return (s['id'],nn,name,(off-t)//sz,(off-t)%sz)
    return (s['id'],nn,'?',off)
def calls(path,sid=None,e='le'):
    secs,info=index(path,e)
    E='<'
    for si,(s,W,nn) in info.items():
        if sid and s['id'] not in sid: continue
        d=s['data']; rel=R.parse(s['reloc'],e); it=dict(rel.internal); ext={so:(a,b) for a,so,b in rel.external}
        print('== script',s['id'],nn)
        for name,t,n,sz in W.arrays:
            if name!='code': continue
            k=0
            while k<n:
                o=t+4*k; w=struct.unpack_from(E+'I',d,o)[0]; op=w>>24; ex=SC.Walk.EXTRA.get(op,0)
                for j in range(ex):
                    a=o+4*(j+1)
                    if a in ext:
                        si2,off=ext[a]; print('  %x op%02x -> %s'%(o,op,resolve(info,si2,off)))
                k+=1+ex
if __name__=='__main__':
    calls(sys.argv[1],set(int(x) for x in sys.argv[2:]) or None)
