import sys,glob,struct
sys.path.insert(0,'/path/to/trudlcport/tools')
import drm
pat=struct.pack('<IIII',0x403,0,0,0x300)
for p in sorted(glob.glob('/path/to/trudlcport/work/baseline/B5/mods/**/*.drm',recursive=True)):
    raw=drm.cdrm_decode(open(p,'rb').read(),'le')
    try: h,secs=drm.sections_with_data(raw,'le')
    except Exception as e: continue
    for s in secs:
        d=s['data']; i=0
        while True:
            i=d.find(pat,i)
            if i<0: break
            print(p.split('mods/')[1],'sec',s['i'],'id',s['id'],'type',s['type'],'off',hex(i),[hex(x) for x in struct.unpack_from('<14I',d,i)] if i+56<=len(d) else '')
            i+=1
