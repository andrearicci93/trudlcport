import sys,struct,pickle,collections
sys.path.insert(0,'/path/to/trudlcport/tools')
from drm import cdrm_decode, sections_with_data
import terrain_convert as TC
T='/path/to/trudlcport/work/baseline/B11/mods/streamgroups/'
YH=TC.yhash_map(); print('yhash entries',len(YH), list(YH.items())[:3])
for f,sid in (('dlc_dungeon_dungeon_main.drm',23805),('dlc_dungeon_dungeon_main.drm',23806),('dlc_dungeon_dungeon_main.drm',23802)):
    raw=cdrm_decode(open(T+f,'rb').read(),'le'); _,secs=sections_with_data(raw,'le')
    s=[s for s in secs if s['type']==12 and s['id']==sid][0]; d=s['data']
    t=TC.parse(d,'<'); 
    import drm_reloc as R; mo=dict(R.parse(s['reloc'],'le').internal)[0xC]; n=struct.unpack_from('<I',d,mo)[0]; mats=struct.unpack_from('<%dI'%n,d,mo+4)
    print(f,sid,'nY',t['nY'],'mats',n)
    for k,y in enumerate(t['Y']):
        m=mats[y[0]] if y[0]<n else None
        if m in (20263,22619,24101): print('  Y',k,'matidx',y[0],'mat',m,'vb',y[1],'hash',hex(y[2]),'in yhash',y[2] in YH,y[3:])
    # distribution of hashes
    c=collections.Counter(hex(y[2]) for y in t['Y']); print('  hash top',c.most_common(4))
print('bounds')
for f in ('dlc_dungeon_dungeon_main.drm','dlc_dungeon_dungeon_to_watertunnel.drm'):
    raw=cdrm_decode(open(T+f,'rb').read(),'le'); _,secs=sections_with_data(raw,'le')
    for s in secs:
        if s['type']==12 and s['data'][0x10:0x14] not in (b'hseM',b'Mesh'):
            d=s['data']; H=struct.unpack_from('<I',d,0)[0]; b=struct.unpack_from('<8f',d,H)
            print(f[-24:],s['id'],len(d),['%.1f'%x for x in b])
