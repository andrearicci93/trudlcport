import sys,struct,pickle,collections,json
sys.path.insert(0,'/path/to/trudlcport/tools')
from drm import cdrm_decode, sections_with_data
import drm_reloc as R, material_reslot as MR, tex_convert as T
rows=[l.rstrip('\n').split('\t') for l in open('../rebuild/installed_effective.tsv')][1:]
tf={}
mats=[]
for r in rows:
    if not r[0].endswith('.drm') or r[0]=='generalbank.drm': continue
    raw=cdrm_decode(open(r[4],'rb').read(),'le'); _,ps=sections_with_data(raw,'le')
    for s in ps:
        if s['type']==5:
            h=T.parse_pc(s['data']); tf[s['id']]=(h['flags'],h['w'],h['h'],hex(h['fmt']))
        elif s['type']==10: mats.append((r[0],s))
c=collections.Counter(); bad=collections.defaultdict(set)
for f,s in mats:
    rel=R.parse(s['reloc'],'le')
    for o,tid,ty,slot in MR.tex_entries(s['data'],rel,'<'):
        t=tf.get(tid)
        if not t: continue
        cube=bool(t[0]&0x8000)
        c[(ty,cube)]+=1
        if (ty==4)!=cube: bad[(ty,cube)].add((s['id'],tid,f))
print(c)
for k,v in bad.items(): print(k,len(v),sorted(v)[:12])
