import json,collections
F=json.load(open('out/feat.json')); C=json.load(open('out/census.json'))
for k,r in sorted(F.items(),key=lambda kv:-sum(C[kv[0]]['refs'].values())):
    if r['xt']: continue
    bb=[n.split('_')[-1] for n in r['pc_samp'] if 'BackBuffer' in n or 'Depth' in n]
    if bb: print(k,sum(C[k]['refs'].values()),C[k]['drm'][:2],bb,r['tex'][:4])
print(sum(1 for k,r in F.items() if not r['xt']),'base-PC mats; refs total',sum(sum(C[k]['refs'].values()) for k,r in F.items() if not r['xt']))
print('refs conv',sum(sum(C[k]['refs'].values()) for k,r in F.items() if r['xt']))
z=[k for k in F if sum(C[k]['refs'].values())==0]; print('zero-mesh-ref mats',len(z),z[:40])
