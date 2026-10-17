import sys,struct,pickle,collections
sys.path.insert(0,'/path/to/trudlcport/tools')
import numpy as np
from drm import cdrm_decode, sections_with_data
import tex_convert as T, drm_reloc as R, material_reslot as MR
rows=[l.rstrip('\n').split('\t') for l in open('../rebuild/installed_effective.tsv')][1:]
tinfo={}; meshref=collections.defaultdict(set); matref=collections.defaultdict(set)
for r in rows:
    if not r[0].endswith('.drm') or r[0]=='generalbank.drm': continue
    raw=cdrm_decode(open(r[4],'rb').read(),'le'); _,ps=sections_with_data(raw,'le')
    for s in ps:
        if s['type']==5 and s['id'] not in tinfo:
            im=T.pc_image(s['data']); rgb=im[...,:3].astype(float); h=T.parse_pc(s['data'])
            tinfo[s['id']]=((rgb.max(2)-rgb.min(2)).mean(), r[0], h['w'],h['h'],hex(h['fmt']), h['flags'])
        elif s['type']==12 and s['reloc']:
            rel=R.parse(s['reloc'],'le')
            for t,o in rel.idref+rel.idref_a:
                if t==5: meshref[struct.unpack_from('<I',s['data'],o)[0]].add(s['id'])
        elif s['type']==10 and s['reloc']:
            rel=R.parse(s['reloc'],'le')
            for o,tid,ty,slot in MR.tex_entries(s['data'],rel,'<'): matref[tid].add((s['id'],ty))
c=[(v[0],k) for k,v in tinfo.items() if k not in meshref and any(t!=3 for _,t in matref.get(k,[]))]
c.sort(reverse=True)
for sat,k in c[:25]: print(k,round(sat,1),tinfo[k][1:],sorted(matref.get(k,[]))[:4])
print('mesh-listed',len(meshref))
