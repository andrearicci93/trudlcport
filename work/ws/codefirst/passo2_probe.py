import sys, struct, glob, os, collections; sys.path.insert(0,'/path/to/trudlcport/tools')
sys.path.insert(0,'/path/to/trudlcport/work/ws/shader4'); sys.path.insert(0,'/path/to/trudlcport/work/ws/contratti')
import drm_write
B='/path/to/trudlcport/work/baseline/B87_materiali19/mods'
def secs(path):
    d=drm_write.read(open(path,'rb').read(),'le'); return d, [(i,s) for i,s in enumerate(d.sections)]
for mid in (20262, 21164, 20345, 21118, 24275):
    print('=== materiale', mid)
    for p in sorted(glob.glob(B+'/**/*.drm', recursive=True)):
        try: d,ss=secs(p)
        except Exception: continue
        for i,s in ss:
            if s.type==10 and s.id==mid:
                lib=struct.unpack_from('<I',s.data,0x30)[0]; pos2=struct.unpack_from('<4I',s.data,0x28)
                libs_here=[x.id for _,x in ss if x.type==9]
                first9=min([i2 for i2,x in ss if x.type==9] or [-1])
                print('  %s: idx %d len %d md5 %s pos2(0x28..)=%s lib0x30=%d | lib presente nel DRM: %s | n.lib9=%d first9=%d' % (os.path.relpath(p,B), i, len(s.data), __import__('hashlib').md5(s.data).hexdigest()[:8], pos2, lib, lib in libs_here, len(libs_here), first9))
