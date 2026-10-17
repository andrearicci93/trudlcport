# Mappa posizionale: k-esima sezione tipo 9 del DRM PC (B43) <-> k-esima del DRM Xbox d'origine (raw_dlc).
# Verifica ordine: per ogni coppia, il pc della mappa per l'id Xbox deve valere l'id PC.
import sys, os, json, collections
ROOT = '/path/to/trudlcport'
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import drm_write
from convert_dlc import raw_dlc
MODS = os.path.join(ROOT, 'work/baseline/B43/mods')
m = json.load(open(os.path.join(ROOT, 'work/render/dlc_shader_map.json')))
pairs = []; skip = collections.Counter(); ok = bad = 0; drms = 0
for root, _, fs in os.walk(MODS):
    for f in fs:
        if not f.endswith('.drm'): continue
        p = os.path.join(root, f)
        pc = drm_write.read(open(p, 'rb').read(), 'le')
        pc9 = [s.id for s in pc.sections if s.type == 9]
        if not pc9: continue
        raw, pk = raw_dlc(f)
        if raw is None: skip['no xbox source'] += 1; continue
        xb = drm_write.read(raw, 'be')
        xb9 = [s.id for s in xb.sections if s.type == 9]
        if len(xb9) != len(pc9): skip['count differs'] += 1; print('COUNT', f, len(xb9), len(pc9)); continue
        drms += 1
        for k, (x, y) in enumerate(zip(xb9, pc9)):
            e = m.get(str(x))
            if e is None: skip['xbox id not in map'] += 1; continue
            if e['pc'] == y: ok += 1
            else: bad += 1
            pairs.append((f, k, x, y, e['cls']))
print('DRMs matched', drms, 'pairs', len(pairs), 'pc agrees', ok, 'disagrees', bad, dict(skip))
json.dump(pairs, open(os.path.join(ROOT, 'work/ws/shader3/positional_pairs.json'), 'w'))
ids = {x for _, _, x, _, _ in pairs}
c = collections.Counter(cl for _, _, x, _, cl in pairs if True)
u = {}
for f, k, x, y, cl in pairs: u[x] = cl
cu = collections.Counter(u.values())
print('distinct xbox lib ids', len(u), dict(cu), 'surrogates', sum(v for k, v in cu.items() if k not in 'AB'))
