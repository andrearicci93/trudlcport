import struct,sys
from minidump.minidumpfile import MinidumpFile
m=MinidumpFile.parse('/path/to/trudlcport/work/crash/rc_try2_dungeon.dmp')
R=m.get_reader()
def rd(a,n):
    try: return R.read(a,n)
    except Exception as e: return None
def u32(a):
    b=rd(a,4); return struct.unpack('<I',b)[0] if b else None
