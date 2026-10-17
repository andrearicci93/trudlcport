import sys,struct
sys.path.insert(0,'/path/to/trudlcport/tools')
import dtpid_sweep as DS, dlc_generic as DG, drm_reloc as R, dtp_audit as A, generic_type0 as G0
st,ids=DS.ctx(); ids.local={}
T=DG.table()
for rel,sid,off in (('dlc_dungeonhalla.drm',20493,0x6630),('dlc_dungeonhalla.drm',20493,0x65f0),('dlc_dungeonhallb.drm',20133,0x5b40),('dlc_dungeonhallb.drm',20133,0x5b00),('dlc_caverns.drm',20872,0x54b0),('dlc_caverns.drm',20872,0x5470)):
    xs=A.xsecs(rel)
    k=[i for i,x in enumerate(xs) if x['id']==sid and x['type']==7][0]
    labs0=G0.labels(xs,'be')
    s=xs[k]; rl=R.parse(s['reloc'],'be')
    stats=__import__('collections').Counter()
    d=G0.convert_section0(s['data'],labs0[k],rl,G0.table7(),ids,T,stats)
    w=off+0x30
    key=[(ww,kk,ck) for ww,kk,ck in G0.G.word_keys(len(s['data']),labs0[k]) if ww==w][0]
    c,src=G0.lookup(G0.table7(),T,key[1],key[2],s['data'][w:w+4])
    print(rel,hex(off),'x',s['data'][w:w+4].hex(),'conv',d[w:w+4].hex(),'class',c,src,'shape',G0.shape(s['data'][w:w+4]))
    print('   key',key[1],key[2])
