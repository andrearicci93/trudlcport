import sys,struct,glob,os,collections
sys.path.insert(0,'/path/to/trudlcport/tools')
import drm, drm_reloc as R
NAME=b'unit'
def inst_info(secs,e='le'):
    E='<' if e=='le' else '>'
    for s in secs:
        if s['type']!=8 or not s['data'] or s['size']<0x50: continue
        d=s['data']
        rel=R.parse(s['reloc'],e); it=dict(rel.internal)
        if 0x10 not in it: continue
        t=it[0x10]; z=d.find(b'\0',t)
        if d[t:z]!=NAME: continue
        if 0x38 not in it: continue
        ft=it[0x38]; n=struct.unpack_from(E+'I',d,ft-4)[0]
        return s['i'],ft,n
    return None
def scan(secs,e='le',want=(12,13)):
    ii=inst_info(secs,e)
    if not ii: return []
    si,ft,n=ii; out=[]
    for s in secs:
        if s['type']!=8 or not s['data'] or s['i']==si: continue
        rel=R.parse(s['reloc'],e)
        for tsi,so,do in rel.external:
            if tsi==si and ft<=do<ft+28*n:
                k=(do-ft)//28
                if k in want: out.append((s['id'],so,k))
    return out
if __name__=='__main__':
    for p in sys.argv[1:]:
        raw=drm.cdrm_decode(open(p,'rb').read(),'le'); h,secs=drm.sections_with_data(raw,'le')
        r=scan(secs)
        if r: print(os.path.basename(p),r)
