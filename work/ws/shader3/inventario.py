# Inventario ufficiale (regola utente): id tipo 9 delle sorgenti Xbox (raw_dlc) per DRM di B43, dedup per id Xbox, classe da dlc_shader_map.json.
import sys, os, json, collections
ROOT = '/path/to/trudlcport'
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import drm_write
from convert_dlc import raw_dlc
MODS = os.path.join(ROOT, 'work/baseline/B43/mods')
m = json.load(open(os.path.join(ROOT, 'work/render/dlc_shader_map.json')))
where = collections.defaultdict(set); nosrc = []; unmapped = set(); errs = []
for root, _, fs in os.walk(MODS):
    for f in fs:
        if not f.endswith('.drm'): continue
        try:
            raw, pk = raw_dlc(f)
            if raw is None: nosrc.append(f); continue
            xb = drm_write.read(raw, 'be')
        except Exception as ex:
            errs.append((f, str(ex))); continue
        for s in xb.sections:
            if s.type != 9: continue
            where[s.id].add(f)
            if str(s.id) not in m: unmapped.add(s.id)
cnt = collections.Counter(m[str(i)]['cls'] for i in where if str(i) in m)
print('DRM senza sorgente Xbox:', len(nosrc), '| errori lettura:', len(errs))
print('id Xbox distinti (tipo 9):', len(where), '| non in mappa:', len(unmapped))
print('per classe (ufficiale):', dict(cnt), '| surrogati C/D:', sum(v for k, v in cnt.items() if k not in 'AB'))
with open(os.path.join(ROOT, 'work/ws/shader3/inventario.tsv'), 'w') as o:
    o.write('id_xbox\tclasse\tid_pc\tdrm\n')
    for i in sorted(where):
        e = m.get(str(i))
        o.write('%d\t%s\t%s\t%s\n' % (i, e['cls'] if e else 'NA', e['pc'] if e else '', ','.join(sorted(where[i]))))
json.dump({'nosrc': nosrc, 'errs': errs}, open(os.path.join(ROOT, 'work/ws/shader3/inventario_meta.json'), 'w'))
