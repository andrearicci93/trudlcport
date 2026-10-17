import sys,struct
sys.path.insert(0,'/path/to/trudlcport/tools')
import drm
R='/path/to/trudlcport/work/baseline/'
base,name,idx,off,n=sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4],0),int(sys.argv[5],0)
sc=drm.sections_with_data(drm.cdrm_decode(open(R+base+'/mods/'+name,'rb').read(),'le'),'le')[1]
d=sc[idx]['data']; print('type',sc[idx]['type'],'id',sc[idx]['id'],'size',len(d))
for o in range(max(0,off-n)&~15, min(len(d),off+n), 16):
    w=struct.unpack_from('<4I',d,o); print('%05x'%o,' '.join('%08x'%x for x in w), ''.join(chr(c) if 32<=c<127 else '.' for c in d[o:o+16]))
