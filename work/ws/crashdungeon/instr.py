import sys,struct,collections
sys.path.insert(0,'/path/to/trudlcport/tools')
import numpy as np
import dtpid_sweep as DS, dlc_generic as DG, dtp_audit as A, drm_reloc as R
st,ids=DS.ctx(); ids.local={}
rel='streamgroups/dlc_dungeon_dungeon_main.drm'
xs=A.xsecs(rel)
have=collections.defaultdict(set)
for q in xs: have[q['type']].add(q['id'])
s=[x for x in xs if x['id']==23793][0]
xd=s['data']; n=len(xd)//4; xw=np.frombuffer(xd,'>u4',n)
cands=DG.analog_index(st,ids).get((7,len(xd),DG._reloc_sig(s['reloc'],'be')),())
ranked=sorted((int(np.count_nonzero(np.frombuffer(st['xb_store'][7,x]['data'],'>u4',n)!=xw)),x) for x in cands)
print('ranked (ndiff, xbox id, pc id)',[(d,x,ids.base[7][x]) for d,x in ranked])
for d,ax in ranked[:1]:
    aw=np.frombuffer(st['xb_store'][7,ax]['data'],'>u4',n)
    pa=st['pc_store'][7,ids.base[7][ax]]['data']; pw=np.frombuffer(pa,'<u4',len(pa)//4)
    rx=R.parse(s['reloc'],'be'); skx=set(rx.pointer_offsets())|set(rx.id_offsets())
    diff=[int(i)*4 for i in np.nonzero(aw!=xw)[0] if int(i)*4 not in skx]
    print('analog',ax,'diff offs',[hex(o) for o in diff],[(int(aw[o//4]),int(xw[o//4])) for o in diff])
    for o in diff:
        vb=int(aw[o//4]); vd=int(xw[o//4])
        opts=[(ty,m[vb]) for ty,m in sorted(ids.base.items()) if isinstance(ty,int) and ty<100 and vb in m and all(vd in have.get(ty,()) for _ in [0])]
        print('off',hex(o),'vb',vb,'vd',vd,'opts',opts,'; vb in base types',[ty for ty,m in sorted(ids.base.items()) if isinstance(ty,int) and ty<100 and vb in m],'; vd in have types',[ty for ty in sorted(have) if vd in have[ty]])
        ox=[int(i)*4 for i in np.nonzero(aw==vb)[0] if int(i)*4 not in skx]
        print(' occurrences of vb in analog xbox',[hex(a) for a in ox])
        for ty,vp in opts:
            op=[int(i)*4 for i in np.nonzero(pw==vp)[0]]; print('  ty',ty,'vp',vp,'pc occurrences',[hex(a) for a in op])
print('ANALOG_TRIES',DG.ANALOG_TRIES)
rx=R.parse(s['reloc'],'be')
for d,ax in ranked:
    r=DG._analog_build(xd,xw,rx,ax,n,ids,st,have)
    aw=np.frombuffer(st['xb_store'][7,ax]['data'],'>u4',n)
    diff=[int(i)*4 for i in np.nonzero(aw!=xw)[0]]
    pa=st['pc_store'][7,ids.base[7][ax]]['data']
    print(ax,'diff',[(hex(o),int(aw[o//4]),int(xw[o//4])) for o in diff],'->', r if isinstance(r,str) else ('ok word@0x10=%d'%struct.unpack_from('<I',r[0],16)[0]), 'pc analog w@0x10',struct.unpack_from('<I',pa,16)[0])
