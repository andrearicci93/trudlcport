import sys,os,struct,re,collections,json
sys.path.insert(0,'/path/to/trudlcport/tools')
from drm import cdrm_decode, sections_with_data
import drm_reloc as R
T='/path/to/trudlcport/'
MODS=T+'work/baseline/B8/mods/'
log=open(T+'work/runs/du_B8_1/engine.log','rb').read().decode('latin1')
i=log.find('Loading PC-W\\dlc_dungeon.drm')
names=[]
for m in re.finditer(r'Loading PC-W\\(\S+\.drm) from mods folder',log[i:]):
    n=m.group(1)
    if n not in names: names.append(n)
files={}
for dp,dn,fn in os.walk(MODS):
    for f in fn:
        if f.lower().endswith('.drm'): files[os.path.relpath(os.path.join(dp,f),MODS).lower().replace('/','\\')]=os.path.join(dp,f)
loaded=[];missing=[]
for n in names:
    k=n.lower()
    (loaded if k in files else missing).append(k)
print('loaded',len(loaded),'missing(not in B8 mods => original game file?)',missing)
mats=collections.defaultdict(lambda: {'drm':set(),'refs':collections.Counter(),'reftypes':collections.Counter()})
for k in loaded:
    p=files[k]
    raw=cdrm_decode(open(p,'rb').read(),'le'); _,secs=sections_with_data(raw,'le')
    short=os.path.basename(k)
    for s in secs:
        if s['type']==10: mats[s['id']]['drm'].add(short)
    for s in secs:
        if s['type']==10: continue
        try: rel=R.parse(s['reloc'],'le')
        except Exception: continue
        for t,o in rel.idref+rel.idref_a:
            if t==10 and o+4<=len(s['data']):
                v=struct.unpack_from('<I',s['data'],o)[0]
                mats[v]['refs'][short]+=1; mats[v]['reftypes'][s['type']]+=1
json.dump({str(k):{'drm':sorted(v['drm']),'refs':dict(v['refs']),'reftypes':dict(v['reftypes'])} for k,v in mats.items()},open('out/census.json','w'))
print(len(mats),'materials ids seen')
