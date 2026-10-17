import sys,struct
from minidump.minidumpfile import MinidumpFile
m=MinidumpFile.parse(sys.argv[1]); rd=m.get_reader()
def u32(a):
    try: return struct.unpack('<I',rd.read(a,4))[0]
    except Exception: return None
def rb(a,n):
    try: return rd.read(a,n)
    except Exception: return None
mg=u32(0xfadfac); print('mgr',hex(mg or 0), 'Lara',hex(u32(0xe7f094) or 0))
if not mg: sys.exit()
def inst(h):
    p=u32(h); g=u32(h+4)
    if not p: return None
    if u32(p+0x44)!=g: return 'STALE'
    return p
seen={}
for i in range(7):
    L=u32(mg+4*i)
    if not L: print('list',i,'null');continue
    cnt=None; c34=u32(L+0x34); 
    n=struct.unpack('<B',rb(c34+4,1))[0] if c34 else 0
    heads=[]
    base=u32(L+0x38)
    for k in range(n): heads.append(('b%d'%k,u32(base+20*k)))
    heads.append(('h',u32(L+0x3c)))
    print('list',i,hex(L),'idx',u32(L),'mask',hex(u32(L+4)),'nsub',n,'[+8]',u32(L+8),'[+c]',u32(L+0xc))
    for nm,h in heads:
        c=0; nd=h
        while nd and c<400:
            hp=nd+8; ins=inst(hp)
            od=u32(ins+0x10) if isinstance(ins,int) else None
            print('   %s node %x ins=%s def=%s id=%s act=%s'%(nm,nd,hex(ins) if isinstance(ins,int) else ins,hex(od) if od else None,u32(nd+0x14),u32(nd+0x18)))
            nd=u32(nd+4); c+=1
print('--- all instances with target points')
reg=set()
for i in range(7):
    L=u32(mg+4*i); c34=u32(L+0x34); n=struct.unpack('<B',rb(c34+4,1))[0] if c34 else 0
    base=u32(L+0x38)
    hs=[u32(base+20*k) for k in range(n)]+[u32(L+0x3c)]
    for nd in hs:
        c=0
        while nd and c<400:
            reg.add((inst(nd+8),i)); nd=u32(nd+4); c+=1
regi={}
for a,i in reg: regi.setdefault(a,[]).append(i)
p=u32(0xd98d54); cnt=0
while p and cnt<5000:
    od=u32(p+0x10); cnt+=1
    nm=u32(od+0x3a)&0xffff if od else 0
    tps=[]
    if od and nm and nm<20:
        ml=u32(od+0x40)
        for j in range(nm):
            mdl=u32(ml+4*j)
            if not mdl: continue
            n=u32(mdl+0x5c)
            if n and n<50:
                pa=u32(mdl+0x60)
                for q in range(n):
                    w=u32(pa+32*q); tps.append((w&0xffff,w>>16,u32(pa+32*q+0x1c)))
    if tps: print('inst %x def %x flags14=%x tps(seg,type,id)=%s registered_lists=%s'%(p,od,u32(p+0x14),tps,regi.get(p)))
    p=u32(p+8)
print('instances',cnt)
