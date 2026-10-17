import sys,struct,pickle,json,collections
sys.path.insert(0,'tools')
import material_reslot as MR, material_convert as MC
L=MR.libs(); XM,PM,DM=L['XM'],L['PM'],L['DM']
W='work/render/'
rules=pickle.load(open(W+'param_rules.pkl','rb'))
smap={int(k):v for k,v in json.load(open(W+'dlc_shader_map.json')).items()}
mx2p=pickle.load(open(W+'material_x2p.pkl','rb'))
mats,msh,_=MR.dlc_tables()
base_tuples=collections.defaultdict(list)
for xm,(d,r) in XM.items(): base_tuples[MC.shader_key(d)].append(xm)
print('rules',len(rules),'base tuples',len(base_tuples))
# for each base tuple: xbox n, pc n set, rule
norule=0; cnt=collections.Counter(); rows=[]
for mid,m in sorted(mats.items()):
    if m['source']!='converted': continue
    d,r=DM[mid]; t=MC.shader_key(d)
    cls=[smap[s]['cls'] if s in smap else 'base' for s in t if s]
    exact=all(c in('A','B') for c in cls)
    if not exact: continue
    bt=tuple(smap[s]['surrogate'] if s in smap else s for s in t)
    nx=struct.unpack_from('>I',d,0x58)[0]; npc=struct.unpack_from('<I',m['data'],0x58)[0]
    seen=bt in base_tuples
    rule=rules.get(bt)
    pcs={struct.unpack_from('<I',PM[mx2p[b]][0],0x58)[0] for b in base_tuples.get(bt,[]) if mx2p.get(b) in PM}
    cnt[(seen, rule is not None)]+=1
    if seen and rule is None: rows.append((mid,bt,nx,npc,sorted(pcs),len(base_tuples[bt])))
    if not seen: rows.append((mid,bt,nx,npc,'unseen',0))
print(cnt)
for r in rows: print(r)
