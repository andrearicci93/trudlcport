# Scansione sezioni tipo 9 dei DRM PC di B43 (sola lettura), dedup per id, classificazione con dlc_shader_map.json.
import sys, os, json, collections
ROOT = '/path/to/trudlcport'
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import drm_write
MODS = os.path.join(ROOT, 'work/baseline/B43/mods')
m = json.load(open(os.path.join(ROOT, 'work/render/dlc_shader_map.json')))
rows = []  # (drm_relpath, lib_id, data_hash)
import hashlib
for root, _, fs in os.walk(MODS):
    for f in fs:
        if not f.endswith('.drm'): continue
        p = os.path.join(root, f)
        try:
            d = drm_write.read(open(p, 'rb').read(), 'le')
        except Exception as ex:
            print('READ FAIL', p, ex); continue
        for s in d.sections:
            if s.type == 9:
                rows.append((os.path.relpath(p, MODS), s.id, hashlib.md5(s.data).hexdigest()))
ids = collections.defaultdict(set)
for rel, i, h in rows: ids[i].add(h)
print('section type 9 total:', len(rows), 'distinct ids:', len(ids), 'ids with >1 content:', sum(1 for v in ids.values() if len(v) > 1))
unm = [i for i in ids if str(i) not in m]
print('ids not in dlc_shader_map:', len(unm))
c = collections.Counter(m[str(i)]['cls'] for i in ids if str(i) in m)
print('by class all DRMs:', dict(c), 'surrogates:', sum(v for k, v in c.items() if k not in 'AB'))
dlc1 = {i for rel, i, h in rows if os.path.basename(rel).startswith(('dlc_', 'dlc1_'))}
c1 = collections.Counter(m[str(i)]['cls'] for i in dlc1 if str(i) in m)
print('dlc_/dlc1_ DRMs: distinct', len(dlc1), dict(c1), 'surrogates:', sum(v for k, v in c1.items() if k not in 'AB'))
json.dump({'rows': rows, 'ids': {str(k): sorted(v) for k, v in ids.items()}}, open(os.path.join(ROOT, 'work/ws/shader3/scan_b43.json'), 'w'))
