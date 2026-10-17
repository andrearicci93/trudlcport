import sys,struct
from minidump.minidumpfile import MinidumpFile
m=MinidumpFile.parse(sys.argv[1]); rd=m.get_reader()
def u32(a):
    try: return struct.unpack('<I',rd.read(a,4))[0]
    except Exception: return None
for a in sys.argv[2:]:
    p=int(a,16)
    print(hex(p),'fields 0x10..0x24:',[hex(u32(p+o)) for o in (0x10,0x14,0x18,0x1c)],'h110..120:',[hex(u32(p+o) or 0) for o in (0x110,0x114,0x118,0x11c,0x120)],'+4c',hex(u32(p+0x4c) or 0),'+54',hex(u32(p+0x54) or 0),'+230',hex(u32(p+0x230) or 0))
