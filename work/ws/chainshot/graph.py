import sys,struct; sys.path.insert(0,'.')
import dump, drm_reloc as R
def load(x, e='>'):
    d=x['data']; rel=R.parse(x['reloc'],'be' if e=='>' else 'le'); it=dict(rel.internal)
    return d,it
def name(d,o):
    z=d.find(b'\0',o); return d[o:z].decode('ascii','replace')
def W(d,o,e='>'): return struct.unpack_from(e+'I',d,o)[0]
def F(d,o,e='>'): return struct.unpack_from(e+'f',d,o)[0]
def node(d,it,o,e='>'):
    # f32 x, f32 y, P name, n1, P a, n2, P b
    nm=it.get(o+8); a=it.get(o+16); b=it.get(o+24)
    return dict(o=o,x=F(d,o,e),y=F(d,o+4,e),name=name(d,nm) if nm is not None else None,na=W(d,o+12,e),a=a,nb=W(d,o+20,e),b=b)
def show_nodes(d,it,o,n,e='>'):
    for i in range(n):
        nd=node(d,it,o+28*i,e)
        print('  node@%x (%.1f,%.1f) %r nA=%d @%s nB=%d @%s'%(nd['o'],nd['x'],nd['y'],nd['name'],nd['na'],hex(nd['a']) if nd['a'] is not None else None,nd['nb'],hex(nd['b']) if nd['b'] is not None else None))
