import json,csv,collections
F=json.load(open('out/feat.json')); C=json.load(open('out/census.json'))
T='/path/to/trudlcport/work/ws/'
pc={r['material']:r for r in csv.DictReader(open(T+'mat2/out/params_count.tsv'),delimiter='\t')}
mt={r['material']:r for r in csv.DictReader(open(T+'mat/out/materials.tsv'),delimiter='\t')}
allc=collections.Counter(); 
for k,r in F.items():
    if r['xt']:
        for n in r['x_const']: allc[n]+=1
print(allc.most_common(40))
pcc=collections.Counter(n for r in F.values() for n in r['pc_const']); print(pcc.most_common(30))
sam=collections.Counter(n for r in F.values() for n in r['pc_samp']); print([n for n in sam if 'Back' in n or 'Depth' in n or 'Refl' in n or 'Env' in n])
rows=[]
for k,r in F.items():
    if not r['xt']: continue
    xl=[n for n in r['x_const'] if 'Light' in n or 'Shadow' in n or 'Irradiance' in n]
    pl=[n for n in r['pc_const'] if 'Light' in n or 'Shadow' in n or 'Irradiance' in n]
    bb=[n for n in r['pc_samp']+r['x_samp'] if 'BackBuffer' in n or 'Depth' in n]
    rows.append((k,sum(C[k]['refs'].values()),bool([n for n in xl if 'Lights' in n]),bool([n for n in pl if 'Lights' in n]),sorted(set(bb)),mt.get(k,{}).get('verdict'),pc.get(k,{}).get('class')))
print('conv in dungeon',len(rows),'Xbox uses p_Lights',sum(1 for r in rows if r[2]),'PC surrogate has p_Lights',sum(1 for r in rows if r[3]))
print('Xbox lit, PC no:',sum(1 for r in rows if r[2] and not r[3]))
for r in sorted(rows,key=lambda r:-r[1]):
    if r[4] or (r[2] and not r[3]): print(r)
