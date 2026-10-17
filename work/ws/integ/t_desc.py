import sys, os
sys.path.insert(0, os.path.expanduser('~/Downloads/tru-port/tools'))
import dtp_audit as A, dtp_schema as S, drm_write as DW
F=os.path.expanduser('~/Downloads/tru-port/work/ws/rebuild/out_fresh2/')
for rel in ('dlc1_uo_dragon_slider.drm','dlc1_uo_raft_bridge.drm'):
    xs=A.xsecs(rel); D=DW.read(open(F+rel,'rb').read(),'le')
    for x,i in A.section_pairs(xs,D):
        if x['type']!=7 or len(D.sections[i].data)!=len(x['data']): continue
        nb,lg=S.convert(x['data'],x['reloc'],D.sections[i].data,D.sections[i].reloc,'D','media')
        for e in lg:
            if e['status']=='CHANGED' : print(rel,D.sections[i].id,e['struct'],e['base'],hex(e['off']),e['field'],e['type'],e['cert'],e['xbox'],e['old'],e['new'],e['status'])
