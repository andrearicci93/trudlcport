import sys,struct
sys.path.insert(0,'/path/to/trudlcport/tools')
import drm, drm_reloc as R, script_conv as SC
def load(path,e='le'):
    raw=drm.cdrm_decode(open(path,'rb').read(),e)
    h,secs=drm.sections_with_data(raw,e)
    return secs
def cstr(d,t):
    z=d.find(b'\0',t); return d[t:z].decode('latin1')
def dump(path,only=None,e='le',verbose=True):
    E='<' if e=='le' else '>'
    secs=load(path,e)
    for s in secs:
        if s['type']!=8 or s['size']<0x50 or s['size']>20000: continue
        if only and s['id'] not in only: continue
        d=s['data']; rel=R.parse(s['reloc'],e)
        try: W=SC.Walk(d,rel,e).run()
        except Exception as ex: print('walk fail',s['id'],ex); continue
        it=dict(rel.internal)
        ext={so:(si,do) for si,so,do in rel.external}
        ids=rel.id_offsets()
        u=lambda o: struct.unpack_from(E+'I',d,o)[0]
        print('== script sec id',s['id'],'size',s['size'],'self',hex(u(0x14)),'super',hex(u(0x18)),'size/align',hex(u(0x1c)), 'vtsize',u(0x3c)&0xffff)
        for off,nm in ((0xc,'nativePkg'),(0x10,'nativeName')):
            t=it.get(off)
            if t is not None: print('  ',nm,cstr(d,t))
        for name,t,n,sz in W.arrays:
            print('  array',name,hex(t),n,sz)
        if verbose:
            for name,t,n,sz in W.arrays:
                if name=='protos':
                    for k in range(n):
                        a=t+k*sz; print('   proto',k,'script',hex(u(a)) if a not in ids else 'ID', 'raw',d[a:a+12].hex(), 'name',hex(u(a+8)))
                if name=='funcs':
                    for k in range(n):
                        a=t+k*sz; pp=it.get(a); print('   func',k,'proto@',hex(pp) if pp is not None else None,'raw',d[a:a+0x1c].hex())
                if name=='code':
                    k=0
                    ops=[]
                    while k<n:
                        o=t+4*k; w=u(o); op=w>>24; ex=SC.Walk.EXTRA.get(op,0)
                        args=[]
                        for j in range(ex):
                            a=o+4*(j+1)
                            tag='ptr->%x'%it[a] if a in it else ('ext->%s'%(ext[a],) if a in ext else ('ID' if a in ids else ''))
                            args.append('%08x%s'%(u(a),(' '+tag) if tag else ''))
                        ops.append('%x: op%02x %06x %s'%(o,op,w&0xffffff,' '.join(args)))
                        k+=1+ex
                    print('   code',hex(t),n); print('\n'.join('     '+x for x in ops))
if __name__=='__main__':
    only=set(int(x) for x in sys.argv[2:]) if len(sys.argv)>2 else None
    dump(sys.argv[1],only)
