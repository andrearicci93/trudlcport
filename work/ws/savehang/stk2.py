import sys,struct
from minidump.minidumpfile import MinidumpFile
m=MinidumpFile.parse('work/crash/save_hang.dmp'); rd=m.get_reader()
mods=[(x.baseaddress,x.baseaddress+x.size,x.name.split('\\')[-1]) for x in m.modules.modules]
tid=int(sys.argv[1]); lo=int(sys.argv[2],16); hi=int(sys.argv[3],16)
t=[t for t in m.threads.threads if t.ThreadId==tid][0]
base=t.Stack.StartOfMemoryRange; sz=t.Stack.MemoryLocation.DataSize
st=rd.read(base,sz)
for k in range(0,sz-3,4):
    a=base+k
    if not(lo<=a<hi): continue
    v=struct.unpack_from('<I',st,k)[0]
    for b,e,n in mods:
        if b<=v<e: print(hex(a),hex(v),n,hex(v-b)); break
