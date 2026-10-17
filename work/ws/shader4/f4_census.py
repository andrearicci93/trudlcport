"""Censimento delle 109 lib surrogate DLC1 (inventario.tsv): posizione, nomi CTAB, illuminata, esito traduzione per slot."""
import sys, os, csv, struct, collections, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from f3_validate import *
import xenos_xlat as XL
LIGHT = ('p_Lights', 'LightEnabled', 'p_ShadowEnabled', 'ParallelShadow', 'Irradiance', 'GlobalAmbientColor', 'ShadowLight', 'NonShadow')
L = libs(); D, DM = L['D'], L['DM']
rows = list(csv.DictReader(open(os.path.join(ROOT, 'work/ws/shader3/inventario.tsv')), delimiter='\t'))
pos = collections.defaultdict(set); users = collections.defaultdict(list)
for mid, (d, r) in DM.items():
    t = struct.unpack_from('>4I', d, 0x28)
    for i in range(4):
        if t[i]: pos[t[i]].add(i); users[t[i]].append(mid)
out = []
for r in rows:
    if r['classe'] not in ('C1', 'C2', 'C3', 'D'): continue
    x = int(r['id_xbox']); lib = D[x]
    e = dict(id=x, cls=r['classe'], pc=r['id_pc'], drm=r['drm'].split(','), kind=lib['kind'], nslots=len(lib['slots']), pos=sorted(pos.get(x, [])), nmat=len(users.get(x, [])))
    names = set(); res = []
    for s in lib['slots']:
        if s == 0xffffffff: res.append(None); continue
        blob = lib['entries'][s]['blob']
        if lib['kind'] == 0: res.append('VS'); continue
        sh = XL.parse(blob)
        for c in sh.ctab: names.add((c['name'], c['set']))
        try:
            tr = xenos2sm3.translate(blob, const_fn)
            res.append('OK(%d)' % tr.ninstr)
        except xenos2sm3.Reject as ex:
            res.append('REJ:' + str(ex)[:60])
        except Exception as ex:
            res.append('ERR:' + repr(ex)[:60])
    e['lit'] = any(any(k in n for k in LIGHT) for n, _ in names)
    e['unknown'] = sorted(n for n, st in names if st == 2 and n not in pc_names())
    e['bools'] = sorted(n for n, st in names if st == 0)
    e['res'] = res
    out.append(e)
json.dump(out, open(os.path.join(HERE, 'f4_census.json'), 'w'), indent=1)
c = collections.Counter()
for e in out:
    key = ('VS' if e['kind'] == 0 else 'PS', tuple(e['pos']), 'lit' if e['lit'] else 'unlit', 'unk' if e['unknown'] else 'known', 'bool' if e['bools'] else 'nobool')
    c[key] += 1
for k, v in sorted(c.items(), key=lambda kv: -kv[1]): print(v, k)
cr = collections.Counter()
for e in out:
    if e['kind'] == 1 and not e['lit'] and not e['unknown'] and not e['bools']:
        for r in e['res']:
            if r: cr[r.split('(')[0] if r.startswith('OK') else r] += 1
print(cr)
