import sys,struct,pickle,collections,re
sys.path.insert(0,'/path/to/trudlcport/tools')
import drm_reloc as R, generic_store
def isname(d,o):
    if o is None or o>=len(d): return None
    z=d.find(b'\0',o,o+40)
    if z<=o: return None
    s=d[o:z]
    if all(32<c<127 for c in s): return s.decode()
    return None
def parse(d,rel,e):
    it=dict(rel.internal)
    nodes=[]
    for s in sorted(it):
        # s = slot of name ptr at node+8
        nm=isname(d,it[s])
        if nm is None: continue
        o=s-8
        if o<0: continue
        if (o+16) in it or (o+24) in it:
            na=struct.unpack_from(e+'I',d,o+12)[0]; nb=struct.unpack_from(e+'I',d,o+20)[0]
            if na>64 or nb>64: continue
            nodes.append((o,nm,na,it.get(o+16),nb,it.get(o+24)))
    return nodes
def trans(d,it,a,na,e):
    out=[]
    for i in range(na):
        p=it.get(a+4*i)
        if p is None: continue
        out.append((p,struct.unpack_from(e+'14I',d,p) if p+56<=len(d) else None))
    return out
def acts(d,it,b,nb,e):
    out=[]
    for i in range(nb):
        o=b+16*i
        if o+16<=len(d): out.append((o,struct.unpack_from(e+'4I',d,o),it.get(o+4)))
    return out
