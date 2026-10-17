import sys; sys.path.insert(0,'.')
import ld, struct, drm_reloc as R
xs=ld.xb()
def X(id, typ=7):
    for x in xs:
        if x['type']==typ and x['id']==id: return x
def dump(id, typ=7, start=0, end=None):
    x=X(id,typ); d=x['data']; rel=R.parse(x['reloc'],'be')
    ptr=dict(rel.internal); ids=set(rel.id_offsets()); ext=set(rel.pointer_offsets())
    end=end or len(d)
    for o in range(start,end,16):
        s=''
        for k in range(0,16,4):
            if o+k>=len(d): break
            w=struct.unpack_from('>I',d,o+k)[0]
            tag=''
            if o+k in ptr: tag='P'
            elif o+k in ids: tag='I'
            elif o+k in ext: tag='E'
            f=struct.unpack_from('>f',d,o+k)[0]
            s+=' %s%08x'%(tag or ' ',w)
        a=d[o:o+16]
        asc=''.join(chr(c) if 32<=c<127 else '.' for c in a)
        print('%04x%s  %s'%(o,s,asc))
    print('internal ptrs:',len(ptr),'ids:',len(ids),'ext:',len(ext))
    return x,rel
if __name__=='__main__':
    dump(int(sys.argv[1]), int(sys.argv[2]) if len(sys.argv)>2 else 7)
