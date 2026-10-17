import sys,struct,glob,os
sys.path.insert(0,'/path/to/trudlcport/tools')
import drm
W='/path/to/trudlcport/work/'
cases=[('dlc_caverns.drm',22,0x54b0),('dlc_dungeonhalla.drm',29,0x6630),('dlc_dungeonhallb.drm',31,0x5b40)]
pat=struct.pack('<IIII',0x403,0,0,0x300)
for d in sorted(glob.glob(W+'mods_*'))+sorted(glob.glob(W+'baseline/*/mods')):
    for f,si,off in cases:
        p=os.path.join(d,f)
        if not os.path.exists(p): continue
        try:
            secs=drm.sections_with_data(drm.cdrm_decode(open(p,'rb').read(),'le'),'le')[1]
            s=secs[si]['data']
            v=struct.unpack_from('<I',s,off+0x30)[0] if s[off:off+16]==pat else 'nomatch'
        except Exception as e: v='err'
        print(os.path.relpath(d,W),f,hex(v) if isinstance(v,int) else v)
