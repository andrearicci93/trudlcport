import sys,struct
from minidump.minidumpfile import MinidumpFile
m=MinidumpFile.parse('work/crash/save_hang.dmp'); rd=m.get_reader()
tid=int(sys.argv[1])
t=[t for t in m.threads.threads if t.ThreadId==tid][0]
base=t.Stack.StartOfMemoryRange; sz=t.Stack.MemoryLocation.DataSize
st=rd.read(base,sz)
for k in range(0,sz-3,4):
    v=struct.unpack_from('<I',st,k)[0]
    if 0x401000<=v<0xd00000:
        try: c=rd.read(v-7,7)
        except Exception: continue
        # call patterns
        kind=None
        if c[2]==0xE8: kind='call rel '+hex((v+struct.unpack_from('<i',c,3)[0])&0xffffffff)
        elif c[1]==0xFF and (c[2]&0x38)==0x10: kind='call ff/2'
        elif c[0]==0xFF and (c[1]&0x38)==0x10: kind='call ff/2 (len3)'
        elif c[5]==0xFF and (c[6]&0x38)==0x10: kind='call ff/2 (len2)'
        elif c[4]==0xFF: kind='call ff? '
        if kind: print(hex(base+k),hex(v),kind)
