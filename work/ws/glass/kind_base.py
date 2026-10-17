import sys,json,struct,collections
sys.path.insert(0,'/path/to/trudlcport/tools'); sys.path.insert(0,'.')
from archive import Archive
from drm import cdrm_decode, sections_with_data
import drm_reloc as R, material_reslot as MR, tex_convert as T
import kind_scan as K
idx=json.load(open('/path/to/trudlcport/work/idx_pc.json'))
pc=Archive('/path/to/trudlcport/pc/bigfile.000','le')
where={}
for r in idx:
    if r[5] and not isinstance(r[5],str):
        for s in r[5]:
            if s[0]==5: where.setdefault(s[1],r)
PM=MR.libs()['PM']
need=set()
for pid,(d,r) in PM.items():
    for o,tid,ty,sl in MR.tex_entries(d,R.parse(r,'le'),'<'): need.add(tid)
print('textures needed',len(need),'found in idx',len([t for t in need if t in where]))
cube={}; cache={}
for tid in sorted(need):
    r=where.get(tid)
    if not r: continue
    key=r[1]
    if key not in cache:
        try:
            raw=cdrm_decode(pc.read(pc.idx[r[1]]),'le'); cache[key]={s['id']:s for s in sections_with_data(raw,'le')[1] if s['type']==5}
        except Exception as e: cache[key]={}
    s=cache[key].get(tid)
    if s: cube[tid]=bool(T.parse_pc(s['data'])['flags']&0x8000)
print('resolved',len(cube))
bad=[]; n=0
for pid,(d,r) in PM.items():
    m=K.mism(d,r,cube); n+=1
    if m: bad.append((pid,m))
print('PC base materials',n,'with kind mismatch',len(bad)); print(bad[:15])
