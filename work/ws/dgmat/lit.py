import json,csv,collections,struct,sys
sys.path.insert(0,'/path/to/trudlcport/tools')
import material_reslot as MR
from shaderlib import constants
L=MR.libs(); X,D=L['X'],L['D']
F=json.load(open('out/feat.json')); C=json.load(open('out/census.json'))
mt={r['material']:r for r in csv.DictReader(open('/path/to/trudlcport/work/ws/mat/out/materials.tsv'),delimiter='\t')}
libs=collections.defaultdict(set); passes=collections.Counter(); refs=collections.Counter()
def lit(lib):
    for s in set(lib['slots'])-{0xFFFFFFFF}:
        v,c=constants(lib['entries'][s]['blob'],'x')
        if any(n=='p_Lights' for n,rs,ri,rc in c): return True
    return False
tot=collections.Counter()
for k,r in F.items():
    if not r['xt'] or k not in mt: continue
    nref=sum(C[k]['refs'].values())
    for p in mt[k]['passes(pos:dlcLib:cls:surrogate:status)'].split():
        pos,lib,cls,sur,stt=p.split(':'); lib=int(lib)
        l=D.get(lib) or X.get(lib)
        isl=bool(l and l['kind']==1 and lit(l))
        libs[(cls,isl)].add(lib); passes[(cls,isl)]+=1; refs[(cls,isl)]+=nref
for k in sorted(libs): print(k,'distinct libs',len(libs[k]),'material-passes',passes[k],'mesh refs',refs[k])
