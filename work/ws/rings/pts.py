import sys,struct
sys.path.insert(0,'/path/to/trudlcport/tools')
import pairs as P, drm_reloc as R
MAGIC={'be':bytes.fromhex('04c20453'),'le':bytes.fromhex('5304c204')}
def pts(secs,e):
    E='>' if e=='be' else '<'
    out=[]
    for s in secs:
        d=s['data']
        if s['type']!=7 or not d or len(d)<0x80 or d[:4]!=MAGIC[e]: continue
        n=struct.unpack_from(E+'I',d,0x5c)[0]
        it=dict(R.parse(s['reloc'],e).internal); a=it.get(0x60)
        if not n or a is None: continue
        for q in range(n):
            o=a+32*q
            out.append((s['id'],q,struct.unpack_from(E+'H',d,o)[0],struct.unpack_from(E+'H',d,o+2)[0],struct.unpack_from(E+'I',d,o+0x1c)[0],struct.unpack_from(E+'3f',d,o+4)))
    return out
if __name__=='__main__':
    for nm in sys.argv[1:]:
        x=P.xbox_drm(nm); p=P.pc_drm(nm)
        print(nm,'xbox',pts(x[1],'be') if x else None)
        print(nm,'pc  ',pts(p[1],'le') if p else None)
