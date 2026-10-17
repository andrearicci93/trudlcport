import csv,collections
rows=list(csv.DictReader(open('work/ws/mat2/out/params_count.tsv'),delimiter='\t'))
d1=[r for r in rows if r['dlc1_units']]
def short(u): return u.replace('.drm','').replace('dlc1_','').replace('dlc_','')
L=[]
L.append('| materiale | DRM DLC1 | mesh | n Xbox -> PC | bytecode c100+ (max/min) | classe | nota |\n|---|---|---|---|---|---|---|')
order={'rotto':0,'rotto-parziale':0,'sospetto-alto':1,'sospetto':2}
bad=[r for r in d1 if r['class']!='OK']
bad.sort(key=lambda r:(order[r['class']],int(r['material'])))
for r in bad:
    L.append('| %s | %s | %s | %s -> %s | %s/%s | %s | %s |'%(r['material'],', '.join(short(u) for u in r['dlc1_units'].split(','))[:70],r['meshes'],r['n_xbox'],r['n_pc'],r['bytecode_need_max'],r['bytecode_need_min'],r['class'],r['reason'].replace('UNVERIFIED ','')))
tb='\n'.join(L)
ok=[r for r in d1 if r['class']=='OK']
by=collections.defaultdict(list)
for r in ok: by[(r['n_xbox'],r['n_pc'])].append(r['material'])
L2=['| n Xbox -> PC (== bytecode) | materiali |','|---|---|']
for k,v in sorted(by.items(),key=lambda kv:(int(kv[0][1]),int(kv[0][0]))): L2.append('| %s -> %s | %s |'%(k[0],k[1],' '.join(sorted(v,key=int))))
open('work/ws/mat2/scratch/tables.md','w').write('### Non OK (DLC1, %d)\n\n%s\n\n### OK (DLC1, %d)\n\n%s\n'%(len(bad),tb,len(ok),'\n'.join(L2)))
c=collections.Counter(r['class'] for r in d1); print(c, len(d1))
print(collections.Counter((r['class'],'trunc' if 'troncato' in r['reason'] else ('pad' if 'padded' in r['reason'] else 'eq')) for r in d1 if r['class']!='OK'))
