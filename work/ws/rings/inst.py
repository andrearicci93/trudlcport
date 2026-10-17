import sys,struct
from minidump.minidumpfile import MinidumpFile
import os
m=MinidumpFile.parse(os.environ.get('DMP','/path/to/trudlcport/work/crash/save_hang.dmp')); rd=m.get_reader()
def rb(a,n):
    try: return rd.read(a,n)
    except Exception: return None
def u32(a):
    b=rb(a,4); return struct.unpack('<I',b)[0] if b else None
def f32(a):
    b=rb(a,4); return struct.unpack('<f',b)[0] if b else None
if __name__=='__main__':
    names={0xd106c0:'A1',0xd109b0:'B1R',0xd10ca0:'C1',0xd10f90:'A2',0xd11280:'B2R',0xd11570:'C2',0xd11860:'A3',0xd11b50:'B3R',0xd11e40:'C3',0xd12130:'A4',0xd12420:'B4R',0xd12710:'C4',0xd12a00:'A5',0xd12cf0:'B5R',0xd12fe0:'C5'}
    adr=sorted(names)
    D={a:rb(a,0x2f0) for a in adr}
    print('offs where values differ among instances (hex words) - first 0x2f0 bytes')
    for off in range(0,0x2f0,4):
        row=[struct.unpack('<I',D[a][off:off+4])[0] for a in adr]
        if len(set(row))>1:
            print('%03x'%off,' '.join('%s=%08x'%(names[a],v) for a,v in zip(adr,row)))
