import sys,struct; sys.path.insert(0,'/path/to/trudlcport/tools')
import drm_reloc as R
STR={0:36,1:68,2:32,3:56,4:0}
def hinfo(d,rel,endian):
    e='>' if endian=='be' else '<'
    it=dict(rel.internal)
    seg=it.get(0xc); n=struct.unpack_from(e+'I',d,4)[0]
    out=[]
    tg=sorted(set(it.values())|{len(d)})
    for j in range(n):
        h=it.get(seg+0x40*j+0x3c)
        row={'seg':j,'h':h,'arrs':[]}
        if h is not None:
            for k in range(5):
                c=struct.unpack_from(e+'I',d,h+8*k)[0]; a=it.get(h+8*k+4)
                if c and a is not None:
                    nx=min([v for v in tg if v>a],default=len(d))
                    row['arrs'].append((k,c,a,(nx-a)//c))
        out.append(row)
    return out
def show(d,rel,endian,label=''):
    e='>' if endian=='be' else '<'
    print('==',label,'len',len(d))
    for row in hinfo(d,rel,endian):
        seg=dict(rel.internal)[0xc]+0x40*row['seg']
        print(' seg',row['seg'],'segdata',' '.join('%08x'%struct.unpack_from(e+'I',d,seg+4*q)[0] for q in range(16)))
        for k,c,a,st in row['arrs']:
            sz=STR.get(k) or st
            for i in range(c):
                o=a+i*sz
                print('   arr%d[%d] @%x'%(k,i,o),' '.join('%08x'%struct.unpack_from(e+'I',d,o+4*q)[0] for q in range(sz//4)))
