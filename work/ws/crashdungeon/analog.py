import sys,os,struct,collections
sys.path.insert(0,'/path/to/trudlcport/tools')
import dtpid_sweep as DS, dlc_generic as DG, drm_reloc as R
st,ids=DS.ctx()
rel='streamgroups/dlc_dungeon_dungeon_main.drm'
import dtp_audit as A
xs=A.xsecs(rel)
for sid in (23793,23613):
    s=[x for x in xs if x['id']==sid][0]
    sig=DG._reloc_sig(s['reloc'],'be')
    cands=DG.analog_index(st,ids).get((7,len(s['data']),sig),())
    print(sid,'reloc',R.parse(s['reloc'],'be').pointer_offsets(),R.parse(s['reloc'],'be').id_offsets(),'analogs',len(cands))
    cnt=collections.Counter()
    for x in cands:
        ad=st['xb_store'][7,x]['data']; pd=st['pc_store'][7,ids.base[7][x]]['data']
        if len(pd)!=len(ad): continue
        xw=struct.unpack('>9I',ad[:36]); pw=struct.unpack('<9I',pd[:36])
        cnt[(xw[4],pw[4],xw[8],pw[8], xw[0])]+=1
    print(cnt.most_common(12))
