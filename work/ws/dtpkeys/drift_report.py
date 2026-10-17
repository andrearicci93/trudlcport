import json, collections, sys
sys.path.insert(0,'tools')
import dtp_keys as K
rows=json.load(open('work/ws/dtpkeys/drift_rows.json'))
def verdict(r):
    ev=[]
    for src,m in (('local',r['loc'][0] if 'loc' in r else None),('rule',r['rule'][1] if 'rule' in r else None)):
        if not m: continue
        ev.append((src, bool(r['ci']&m), bool(r['cf']&m)))
    if r['ci']==0 or r['cf']==0:
        # one side is not a byte permutation (id remap etc.)
        return 'REVIEW_nonperm', 'low', ev
    if not ev: return 'UNDECIDED', 'none', ev
    vs=set()
    for s,i,f in ev:
        vs.add('inst' if i and not f else 'fresh' if f and not i else 'both' if i and f else 'neither')
    if len(vs)==1:
        v=vs.pop(); cert='high' if len(ev)==2 else ('medium' if ev[0][0]=='local' and r['loc'][1]>=3 else 'medium-low')
        return v,cert,ev
    return 'CONFLICT','low',ev
out=collections.Counter(); tab=collections.Counter()
for r in rows:
    r['verdict'],r['cert'],_=verdict(r)
    tab[(r['verdict'],r['cert'])]+=1
print(sorted(tab.items(),key=lambda x:-x[1]))
bf=collections.defaultdict(collections.Counter)
for r in rows: bf[r['file']][r['verdict']+'/'+r['cert']]+=1
for f,c in sorted(bf.items(),key=lambda x:-sum(x[1].values())): print('%-50s %s'%(f,dict(c)))
json.dump(rows,open('work/ws/dtpkeys/drift_verdict.json','w'))
