import sys, os, hashlib, struct
sys.path.insert(0,'tools'); sys.path.insert(0,'work/ws/webs')
import drm_write as DW, drm_reloc as R, build, drm as D1, web_cutout as WC
OUT='work/ws/webs/out'; B8='work/baseline/B8/mods'; B9='work/baseline/B9/mods'
def rd(p): return DW.read(DW.cdrm_decode(open(p,'rb').read(),'le'),'le')
ref=rd(B8+'/dlc_caverns.drm'); R6610=[s for s in ref.sections if s.type==5 and s.id==6610][0]
R23173=[s for s in ref.sections if s.type==10 and s.id==23173][0]
B9CH={'streamgroups/dlc_water_wheel_waterwheel_main.drm','dlc_caverns_hall.drm','streamgroups/dlc_pillory_pillorymain.drm','streamgroups/dlc_pillory_pillory_b.drm'}
for l in open(OUT+'/md5.txt'):
    m,rel=l.split(None,1); rel=rel.strip()
    data=open(os.path.join(OUT,rel),'rb').read(); assert hashlib.md5(data).hexdigest()==m
    N=rd(os.path.join(OUT,rel)); S=rd(os.path.join(B9 if rel in B9CH else B8,rel)); O=rd(os.path.join(B8,rel))
    assert [(s.type,s.id) for s in N.sections]==[(s.type,s.id) for s in S.sections]
    diff=[(a.type,a.id) for a,b in zip(S.sections,N.sections) if a.data!=b.data or a.reloc!=b.reloc]
    # meta equality
    for a,b in zip(S.sections,N.sections):
        for k in ('type','id'): assert getattr(a,k)==getattr(b,k)
    t=[s for s in N.sections if s.type==5 and s.id==6610][0]
    ok6610=(t.data==R6610.data and t.reloc==R6610.reloc)
    m23=[s for s in N.sections if s.type==10 and s.id==23173]
    ok23=[(s.data==R23173.data, s.reloc==R23173.reloc) for s in m23]
    # reloc sanity for changed materials
    rs=[]
    for s in N.sections:
        if s.type==10 and (s.type,s.id) in diff:
            rl=R.parse(s.reloc,'le'); n=len(s.data)
            assert all(0<=o<n and 0<=t_<=n for o,t_ in rl.internal)
            assert all(0<=o<n for _,o in rl.idref+rl.idref_a)
            rs.append(s.id)
    # independent parser
    try: d1=D1.read(DW.cdrm_decode(data,'le')) if hasattr(D1,'read') else None
    except Exception as e: d1='ERR %s'%e
    # vs B8: sections differing
    vsb8=[(a.type,a.id) for a,b in zip(O.sections,N.sections) if a.data!=b.data or a.reloc!=b.reloc]
    print(rel,'diff vs source',diff,'| vs B8',vsb8,'| 6610==caverns',ok6610,'| 23173==caverns(data,reloc)',ok23,'| reloc ok',rs)
# idempotency on B8 already-cut DRMs
for rel in ['dlc_caverns.drm','dlc_caverns_hall.drm','streamgroups/dlc_water_wheel_waterwheel_main.drm']:
    raw=DW.cdrm_decode(open(os.path.join(B8,rel),'rb').read(),'le')
    new,rep=build.patch(raw)
    print('idemp',rel,[r for r in rep], 'bytes identical:',new==raw)
    try: new2,_=WC.patch(raw); print('   web_cutout originale riapplicato identico:',new2==raw)
    except AssertionError as e: print('   web_cutout originale riapplicato: AssertionError (non idempotente)')
