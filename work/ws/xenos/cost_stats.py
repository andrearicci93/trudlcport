"""(4) Cost statistics for a REAL Xenos -> D3D9 SM3 conversion of the DLC1 shader libs not already covered by an identical base lib (classes C1/C2/C3/D).
Output: printed tables + out/cost_stats.json.   usage: tools/venv/bin/python -I work/ws/xenos/cost_stats.py"""
import sys, os, json, collections, struct, re
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, 'tools'))
import xenos_xlat as X
from shaderlib import norm_name, constants
L = X.load_libs()
cen = json.load(open(os.path.join(HERE, 'out', 'census.json')))
smap = {int(k): v for k, v in json.load(open(os.path.join(ROOT, 'work/render/dlc_shader_map.json'))).items()}
# PC constant names (union over all PC libs) and their registers
pcnames = collections.defaultdict(set)
for lid, lib in L['P'].items():
    for s in set(lib['slots']) - {0xffffffff}:
        v, c = constants(lib['entries'][s]['blob'], 'p')
        for n, rs, ri, rc in c: pcnames[norm_name(n)].add((rs, ri))
# position of use
pos = collections.defaultdict(set)
for mid, (d, r) in L['DM'].items():
    for i, s_ in enumerate(struct.unpack_from('>4I', d, 0x28)):
        if s_: pos[s_].add(i)
rows = []
agg = collections.Counter(); hist = collections.defaultdict(list)
names_missing = collections.Counter()
for r in cen:
    if r['cls'] in ('A', 'B'): continue
    lib = L['D'][r['id']]
    for s in set(lib['slots']) - {0xffffffff}:
        sh = X.parse(lib['entries'][s]['blob'])
        ev = X.walk(sh)
        n_alu = sum(1 for e in ev if e[0] == 'alu'); n_f = sum(1 for e in ev if e[0] == 'fetch')
        maxr = 0
        for e in ev:
            if e[0] == 'alu':
                f = e[2]
                maxr = max(maxr, f['vdest'] if not f['export'] else 0, f['sdest'] if not f['export'] else 0)
            elif e[0] == 'fetch': maxr = max(maxr, X.bits(e[2], 12, 6))
        kind = 'PS' if sh.is_ps else 'VS'
        miss = []
        maxf = max([c['reg'] + c['count'] for c in sh.ctab if c['set'] == 2] or [0])
        for c in sh.ctab:
            nn = norm_name(c['name'])
            if c['set'] == 3: continue            # samplers: names are per-material, handled by reslot
            if nn not in pcnames: miss.append(nn)
        for m in miss: names_missing[m] += 1
        f = X.summary(sh)
        hist[kind, 'instr'].append(n_alu + n_f); hist[kind, 'maxtemp'].append(maxr + 1); hist[kind, 'ninterp'].append(sh.ninterp); hist[kind, 'maxfloatreg'].append(maxf)
        agg[kind, 'blobs'] += 1
        for k in ('cf:cond_jmp', 'cf:cond_exec', 'cf:cond_exec_pred_clean', 'cf:cond_exec_pred', 'predicated alu', 'v:cube', 'tfetch dimCube', 'const relative', 'v:kill_gt', 'tfetch register gradients', 'tfetch register lod', 'cf:loop_start', 'cf:cond_call', 'cf:return'):
            if f.get(k): agg[kind, k] += 1
        if sh.is_ps and sh.outputs is not None:
            if sh.outputs & 0x10: agg[kind, 'writes depth'] += 1
            if sh.outputs & 0xE: agg[kind, 'MRT'] += 1
        if miss: agg[kind, 'blobs with float/bool/int constant names absent from every PC lib'] += 1
        if any(c['set'] in (0, 1) for c in sh.ctab): agg[kind, 'uses bool/int consts (dynamic flow / loops)'] += 1
libs = collections.Counter(); posd = collections.Counter()
for r in cen:
    if r['cls'] in ('A', 'B'): continue
    libs[(r['cls'], 'PS' if r['kind'] == 1 else 'VS')] += 1
    posd[(r['cls'], tuple(sorted(pos.get(r['id'], []))))] += 1
print('libs by class/kind', dict(libs))
print('use position (tuple slot) per class', dict(posd))
for k, v in sorted(agg.items()): print('  %s %-70s %d' % (k[0], k[1], v))
def q(a): a = sorted(a); return (a[0], a[len(a) // 2], a[int(len(a) * .9)], a[-1]) if a else None
for k, v in sorted(hist.items()): print('  %s %-12s min/median/p90/max %s' % (k[0], k[1], q(v)))
print('top constant names missing from all PC libs:', names_missing.most_common(12))
slots = collections.Counter()
for r in cen:
    if r['cls'] not in ('A', 'B'): slots[r['kind']] += r['nslots']
print('occupied permutation slots (Xbox side) PS/VS:', dict(slots))
json.dump(dict(libs={'%s|%s' % k: v for k, v in libs.items()}, agg={'%s|%s' % k: v for k, v in agg.items()}, miss=names_missing.most_common(40)), open(os.path.join(HERE, 'out', 'cost_stats.json'), 'w'))
