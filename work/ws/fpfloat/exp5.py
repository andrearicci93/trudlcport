import sys; sys.path.insert(0,'work/ws/fpfloat'); sys.path.insert(0,'tools')
from explore import *
name,did=sys.argv[1],int(sys.argv[2])
xs,D,prs=pairs_for(name)
for x,i in prs:
    sec=D.sections[i]
    if sec.id!=did: continue
    xd=x['data']; pd=sec.data; rel=R.parse(x['reloc'],'be')
    slots=set(rel.pointer_offsets())|set(rel.id_offsets())
    cc=collections.Counter(); bad=[]
    for o in range(0,len(xd),4):
        if o in slots: continue
        xw,pw=xd[o:o+4],pd[o:o+4]
        if xw==xw[::-1] and xw==pw: continue
        c=tuple(n for n,pm in N.PERMS.items() if bytes(xw[j] for j in pm)==pw)
        cc[c]+=1
        if 'u32' not in c: bad.append((o,xw.hex(),pw.hex(),c))
    print(cc.most_common(8)); 
    for b in bad: print('  %04x %s %s %s'%b)
