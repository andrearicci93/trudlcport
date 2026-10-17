import sys; sys.path.insert(0,'work/ws/fpfloat'); sys.path.insert(0,'tools')
from explore import *
name,did=sys.argv[1],int(sys.argv[2])
xs,D,prs=pairs_for(name)
for x,i in prs:
    sec=D.sections[i]
    if sec.id!=did: continue
    xd=x['data']; rel=R.parse(x['reloc'],'be'); it=sorted(rel.internal)
    print('size',len(xd),'internal',len(it),'ids',len(rel.id_offsets()),'ptrs',len(rel.pointer_offsets()))
    print([ (hex(o),hex(t)) for o,t in it])
