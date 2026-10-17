"""Summarise out/map_all.json against work/ws/mat/out/scan.json (param_auto verdicts) per DLC1 material.   usage: tools/venv/bin/python -I work/ws/xenos/map_all_report.py"""
import sys, os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
res = {(r['dl'], r['sl']): r for r in json.load(open(os.path.join(HERE, 'out', 'map_all.json')))}
rows = json.load(open(os.path.join(ROOT, 'work/ws/mat/out/scan.json')))
print('pairs run', len(res), 'errors', sum(1 for r in res.values() if 'error' in r))
pc = collections.Counter(); per_pair = {}
for k, r in res.items():
    if 'error' in r: continue
    c = r['cls']; n = r['n']
    voted = n - c.get('NO-VOTE', 0); conf = c.get('CONFLICT', 0)
    st = 'EMPTY(S has no MaterialParams)' if n == 0 else 'FULL-ID' if voted == n and conf == 0 and r['nonident'] == 0 else 'FULL-MAP' if voted == n and conf == 0 else 'PARTIAL' if voted > 0 else 'NONE'
    per_pair[k] = (st, n, voted, conf, r['ident'], r['nonident'])
    pc[st] += 1
print('pair-level (new method):', dict(pc))
mat = collections.Counter(); detail = collections.defaultdict(list)
for m in rows:
    if not m['dlc1']: continue
    sts = []
    for p in m['passes']:
        k = (p[1], p[3])
        if k in per_pair: sts.append(per_pair[k][0])
        elif p[4] == 'EXACT': sts.append('EXACT')
        else: sts.append('NOT-RUN')
    worst = 'NOT-RUN' if 'NOT-RUN' in sts else 'NONE' if 'NONE' in sts else 'PARTIAL' if 'PARTIAL' in sts else 'FULL-MAP' if 'FULL-MAP' in sts else 'FULL-ID' if 'FULL-ID' in sts else 'EMPTY' if any(s.startswith('EMPTY') for s in sts) else 'EXACT'
    mat[(m['verdict'], worst)] += 1
    detail[(m['verdict'], worst)].append(m['mid'])
print('DLC1 materials: param_auto verdict -> new-method worst-pass status')
for k, v in sorted(mat.items()): print('   %-20s -> %-10s %d' % (k[0], k[1], v))
unres = [m for m in rows if m['dlc1'] and m['verdict'] not in ('EXACT', 'IDENTITY-VERIFIED', 'PROVEN-MAP')]
print('DLC1 materials unresolved by param_auto:', len(unres))
for tag in ('FULL-ID', 'FULL-MAP', 'PARTIAL', 'NONE', 'EMPTY', 'NOT-RUN'):
    print('   new method %-9s' % tag, sum(v for (a, b), v in mat.items() if b == tag and a not in ('EXACT', 'IDENTITY-VERIFIED', 'PROVEN-MAP')))
