import sys,struct
sys.path.insert(0,'/path/to/trudlcport/tools')
import dtpid_sweep as DS, dlc_generic as DG, drm_reloc as R, dtp_audit as A
st,ids=DS.ctx()
for rel,sid,off in (('dlc_dungeonhalla.drm',20493,0x6630),('dlc_dungeonhallb.drm',20133,0x5b40),('dlc_caverns.drm',20872,0x54b0)):
    xs=A.xsecs(rel)
    s=[x for x in xs if x['id']==sid and x['type']==7][0]
    print(rel,sid,'in base ids:',sid in ids.base.get(7,{}),'size',len(s['data']))
    ids.local={}
    r=DG.analog_convert(s,xs,ids,st,()) if sid not in ids.base.get(7,{}) else None
    if r:
        d=r[0]; print(' analog route; word', d[off+0x30:off+0x34].hex(), 'xbox', s['data'][off+0x30:off+0x34].hex())
    else: print(' no analog')
    # rel info
    rr=R.parse(s['reloc'],'be')
    print(' ptr at word? ', (off+0x30) in set(rr.pointer_offsets()), (off+0x30) in set(rr.id_offsets()))
