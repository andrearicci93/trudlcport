import sys,struct,pickle,json,collections
sys.path.insert(0,'tools')
import material_reslot as MR, material_convert as MC
L=MR.libs(); XM,PM,DM=L['XM'],L['PM'],L['DM']
W='work/render/'
rules=pickle.load(open(W+'param_rules.pkl','rb'))
smap={int(k):v for k,v in json.load(open(W+'dlc_shader_map.json')).items()}
mx2p=pickle.load(open(W+'material_x2p.pkl','rb'))
mats,msh,_=MR.dlc_tables()
bt_=collections.defaultdict(list)
for xm,(d,r) in XM.items(): bt_[MC.shader_key(d)].append(xm)
def ident(xm):
    d,r=XM[xm]; p=mx2p.get(xm)
    if p not in PM: return None
    pd,pr=PM[p]
    return MC.read_params(d,r,'>')==MC.read_params(pd,pr,'<')
res={}
for t,l in bt_.items():
    v=[ident(x) for x in l]; v=[a for a in v if a is not None]
    res[t]=(sum(v),len(v))
cnt=collections.Counter(); bad=[]
for mid,m in sorted(mats.items()):
    if m['source']!='converted': continue
    d,r=DM[mid]; t=MC.shader_key(d)
    cls=[smap[s]['cls'] if s in smap else 'base' for s in t if s]
    if not all(c in('A','B') for c in cls): continue
    bt=tuple(smap[s]['surrogate'] if s in smap else s for s in t)
    if bt not in res: cnt['unseen']+=1; continue
    a,b=res[bt]
    k='rule' if rules.get(bt) else ('identity all' if a==b else ('identity none' if a==0 else 'identity partial'))
    cnt[k]+=1
    if k.startswith('identity') and k!='identity all': bad.append((mid,bt,a,b))
print(cnt); print(len(bad)); print(bad[:40])
pickle.dump({'res':res},open('work/ws/mat2/scratch/ident.pkl','wb'))
