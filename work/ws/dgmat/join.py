import json,csv,re,collections
T='/path/to/trudlcport/work/ws/'
C=json.load(open('out/census.json'))
pc={r['material']:r for r in csv.DictReader(open(T+'mat2/out/params_count.tsv'),delimiter='\t')}
mt={r['material']:r for r in csv.DictReader(open(T+'mat/out/materials.tsv'),delimiter='\t')}
unb={}
for l in open(T+'glass/scan_B8.txt'):
    m=re.match(r'(\S+) (\d+) (.*)',l)
    if m: unb.setdefault(m.group(2),[]).append(m.group(3)[:0] or ('cube' if 'cube' in m.group(3) else '2d'))
rows=[]
for k,v in C.items():
    if not v['drm']: continue
    nref=sum(v['refs'].values())
    p=pc.get(k,{}); m=mt.get(k,{})
    passes=m.get('passes(pos:dlcLib:cls:surrogate:status)','')
    rows.append((k,','.join(v['drm']),nref,dict(v['reftypes']),m.get('verdict','-'),p.get('class','-'),p.get('n_xbox','-')+'>'+p.get('n_pc','-'),passes,','.join(sorted(set(unb.get(k,[]))))))
rows.sort(key=lambda r:(-r[2]))
with open('out/dungeon_materials.tsv','w') as f:
    f.write('mat\tdrms\trefs\treftypes\tverdict\tparamsclass\tn\tpasses\tunbound\n')
    for r in rows: f.write('\t'.join(map(str,r))+'\n')
print(len(rows),'DLC-defined materials in dungeon level; referenced-but-undefined:',sum(1 for v in C.values() if not v['drm']))
cnt=collections.Counter(r[4] for r in rows);print(cnt)
cnt=collections.Counter(r[5] for r in rows);print(cnt)
for r in rows:
    if r[4] not in('EXACT','-') or r[5] not in('OK','-') or r[8]: print(r[:3],r[3],r[4],r[5],r[6],r[7][:90],r[8])
