import json,collections,os,re
R='/path/to/trudlcport/'
rows=json.load(open(R+'work/ws/mat/out/scan.json'))
names={}
for l in open(R+'work/generic/dlc_names.txt'):
    p=l.split()
    if len(p)>=6 and p[0].startswith('0x'): names[p[0].lower()]=p[-1].replace('\\','/').split('/')[-1]
def nm(u): return names.get(u.lower(),u)
inst=set()
for d in ('vm_mods_expected','mods_current','mods_fix14','mods_glitchfix','mods_next','mods_fix20','mods_fix18'):
    dd=R+'work/'+d
    if os.path.isdir(dd): inst|=set(os.listdir(dd))
inst|=set(os.listdir(R+'work/mods_current_webs')) if os.path.isdir(R+'work/mods_current_webs') else set()
d1=[r for r in rows if r['dlc1']]
ALL=['EXACT','EXACT-UNSEEN','IDENTITY-VERIFIED','PROVEN-MAP','IDENTITY-PARTIAL','CANDIDATE-MAP','CANDIDATE-PARTIAL','CONFLICT','UNDECODABLE','REPORT-ONLY(C3)','REPORT-ONLY(D)']
c_all=collections.Counter(r['verdict'] for r in rows); c1=collections.Counter(r['verdict'] for r in d1)
pc=collections.Counter()
for r in rows:
    for p in r['passes']: pc[p[2],p[4]]+=1
o=[]
o.append(open(R+'work/ws/mat/scratch/report_head.md').read())
o.append("## Numeri per materiale (587 convertiti nuovi; DLC1 = sezione presente in un DRM pack10)\n| verdetto | tutti | DLC1 |\n|---|---|---|")
for k in ALL: o.append("| %s | %d | %d |"%(k,c_all[k],c1[k]))
o.append("\n## Numeri per (libreria DLC, materiale) = pass di PS, stessa unita' del survey 280/16/173 di NOTES (C1+C2+C3+D = 134+86+156+93 = 469 = 280+16+173)\n| verdetto | C1 | C2 | C3 | D |\n|---|---|---|---|---|")
sts=sorted({k[1] for k in pc if k[0] in('C1','C2','C3','D')})
for s in sts: o.append("| %s | %s |"%(s,' | '.join(str(pc[c,s]) for c in ('C1','C2','C3','D'))))
o.append("(Le righe A/B = EXACT: %d pass A, %d pass B, non a rischio per il compilatore.)\n"%(pc['A','EXACT'],pc['B','EXACT']))
cleanv={'EXACT','IDENTITY-VERIFIED','PROVEN-MAP'}
risk=[r for r in d1 if r['verdict'] not in cleanv]
unv=[r for r in d1 if any(f.startswith('UNVERIFIED') for f in r['flags'])]
o.append("Materiali DLC1 con rischio params non risolto: %d su %d (verdetto fuori da EXACT/IDENTITY-VERIFIED/PROVEN-MAP, EXACT-UNSEEN incluso). In piu', rischio SEPARATO e gia' noto: %d materiali DLC1 con flag 'UNVERIFIED params N->M vec4 (copiati+riempiti/troncati)' (colonna flags di materials.tsv; es. 20879/20883/20887/23403 17->13 vec4): non toccati da questo strumento.\n"%(len(risk),len(d1),len(unv)))
by=collections.defaultdict(lambda:[collections.Counter(),set()])
for r in risk:
    for u in r['units']:
        by[u][0][r['verdict']]+=1; by[u][1]|=set(r['mesh_ids'])
o.append("## Impatto per DRM DLC1 (materiali a rischio, mesh distinte che li referenziano)\n'inst' = file presente in uno degli overlay installati/pronti (vm_mods_expected, fix14, glitchfix, next, current, fix18, fix20).\n\n| DRM | inst | materiali a rischio | mesh distinte | dettaglio |\n|---|---|---|---|---|")
for u,(c,ms) in sorted(by.items(), key=lambda kv:-sum(kv[1][0].values())):
    n=nm(u); o.append("| %s | %s | %d | %d | %s |"%(n,'si' if n in inst else 'no/n.d.',sum(c.values()),len(ms),', '.join('%s %d'%kv for kv in sorted(c.items()))))
open(R+'work/ws/mat/REPORT.md','w').write('\n'.join(o)+'\n'+open(R+'work/ws/mat/scratch/report_tail.md').read())
