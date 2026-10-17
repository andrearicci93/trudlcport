import sys,struct
from minidump.minidumpfile import MinidumpFile
m=MinidumpFile.parse('/path/to/trudlcport/work/crash/save_hang.dmp'); rd=m.get_reader()
def u32(a):
    try: return struct.unpack('<I',rd.read(a,4))[0]
    except Exception: return None
def rb(a,n):
    try: return rd.read(a,n)
    except Exception: return None
def s(a):
    b=rb(a,40)
    return b.split(b'\0')[0].decode('latin1') if b else None
p=u32(0xd98d54); c=0
while p and c<6000:
    d=u32(p+0x10); c+=1
    uid=u32(d+0x14) if d else None
    if uid in (844,59,181,299) :
        print('inst %x def %x uid %s serial %x'%(p,d,uid,u32(p+0x44) or 0), 'f14/18/1c',[hex(u32(p+o) or 0) for o in (0x14,0x18,0x1c)],'+4c',hex(u32(p+0x4c) or 0))
        # uid scan
        for o in range(0,0x400,4):
            v=u32(p+o)
            if v in (0x40000061,0x40000062,0x40000063,9789): print('   uid field @+%x = %d'%(o,v))
        a=u32(p+0x2d0); b=u32(a) if a else None; C=u32(b+0x2ec) if b else None
        if C:
            S=C-0x10; sec=u32(S+0x70)==0xf0012345
            T=C-4; comp=u32(T+0x54)==0xfea51b1e
            print('   C %x section_magic %s composite_magic %s'%(C,sec,comp))
            if sec:
                desc=u32(S+0x78); nodes=u32(desc+8); idx=struct.unpack('<i',rb(S+0x84,4))[0]
                print('   SEC %x desc %x +0x52=%s +0x2c=%s nnodes %s idx %d  +80 %x +8c %x +90 %x +d0 %x +dc %s'%(S,desc,rb(desc+0x52,1).hex(),rb(desc+0x2c,1).hex(),u32(desc+4),idx,u32(S+0x80) or 0,u32(S+0x8c) or 0,u32(S+0x90) or 0,u32(S+0xd0) or 0,struct.unpack('<f',rb(S+0xdc,4))[0]))
                print('   nodes',[ s(u32(nodes+28*k+8)) for k in range(u32(desc+4) or 0)],'model idx',rb(desc+0x18,1).hex(),'desc+0x50',rb(desc+0x50,4).hex())
    p=u32(p+8)
print('count',c)
