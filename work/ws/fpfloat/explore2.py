import sys
sys.path.insert(0,'work/ws/fpfloat'); sys.path.insert(0,'tools')
from explore import *
name, did = sys.argv[1], int(sys.argv[2]); lo=int(sys.argv[3],0) if len(sys.argv)>3 else 0; hi=int(sys.argv[4],0) if len(sys.argv)>4 else 1<<30
xs, D, prs = pairs_for(name)
for x,i in prs:
    sec=D.sections[i]
    if sec.id!=did: continue
    xd=x['data']; pd=sec.data; rel=R.parse(x['reloc'],'be'); it=dict(rel.internal)
    slots=set(rel.pointer_offsets())|set(rel.id_offsets())
    nd,_=N.nodes(xd,x['reloc'])
    nodeat={}
    for t,tg in nd: nodeat.setdefault(tg,set()).add(t)
    # print by node record
    for tg in sorted(set(it.values())):
        if tg<lo or tg>hi: continue
        print('REC %#x ntypes_pointing=%s  %s'%(tg, sorted(nodeat.get(tg,[])), 'self-node(type,ptr)=%d'%struct.unpack_from('>I',xd,tg)[0] if tg+4<=len(xd) else ''))
        nxt=[t for t in sorted(set(it.values())) if t>tg]; end=min(nxt[0] if nxt else len(xd), tg+0x48)
        for o in range(tg,end,4):
            xw=xd[o:o+4];pw=pd[o:o+4]
            c=[n for n,pm in N.PERMS.items() if bytes(xw[j] for j in pm)==pw]
            f=struct.unpack('>f',xw)[0]
            print('   +%02x %s x=%s p=%s cls=%s f=%.4g'%(o-tg,'P' if o in slots else ' ',xw.hex(),pw.hex(),','.join(c) if c else 'NONE',f))
    print('--- referrers')
    ref=collections.defaultdict(list)
    for o,t in it.items(): ref[t].append(o)
    for tg in sorted(ref):
        if lo<=tg<=hi:
            print('%#x <- %s'%(tg,[( '%#x'%o, 'prev=%s'%(xd[o-4:o].hex() if o>=4 else None)) for o in ref[tg]]))
