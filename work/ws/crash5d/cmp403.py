import sys,struct,glob
sys.path.insert(0,'/path/to/trudlcport/tools')
import drm, soundplex_fix as SF
B='/path/to/trudlcport/work/baseline/B5/mods/'
cases=[('dlc_caverns.drm',22),('dlc_dungeonhalla.drm',29),('dlc_dungeonhallb.drm',31),('dlc_dungeon.drm',70),('dlc_pillory.drm',34)]
for f,si in cases:
    pc=drm.sections_with_data(drm.cdrm_decode(open(B+f,'rb').read(),'le'),'le')[1]
    xs=SF.xsecs_of(f)
    print(f,'pc secs',len(pc),'xb secs',len(xs) if xs else None)
    if not xs: continue
    p=pc[si]; 
    # find xbox sec same id
    xm=[x for x in xs if x['id']==p['id'] and x['type']==p['type']]
    print(' pc sec',si,p['id'],len(p['data']),'xb match',[(x['i'],len(x['data'] or b'')) for x in xm])
    if not xm: continue
    x=xm[0]; pd=p['data']; xd=x['data']
    i=0
    pat=struct.pack('<IIII',0x403,0,0,0x300)
    while True:
        i=pd.find(pat,i)
        if i<0: break
        pv=struct.unpack_from('<I',pd,i+0x30)[0]; xv=struct.unpack_from('>I',xd,i+0x30)[0] if i+0x34<=len(xd) else None
        xtag=struct.unpack_from('>I',xd,i)[0]
        print('  off',hex(i),'pc',hex(pv),'xbox',hex(xv) if xv is not None else None,'xtag',hex(xtag))
        i+=1
