"""Census of DLC1 (pack ack10.000) shader libs (type 9) in the DLC DRMs. Output: out/census.json"""
import sys, os, pickle, json, collections
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
drms = pickle.load(open(os.path.join(ROOT, 'work', 'generic', 'dlc_drms.pkl'), 'rb'))
libs = collections.defaultdict(set)   # id -> set of drm short names
allpacks = collections.Counter()
for (pack, name, spec), (hdr, secs) in drms.items():
    allpacks[pack] += 1
    if pack != 'ack10.000': continue
    for s in secs:
        if s['type'] == 9: libs[s['id']].add(os.path.basename(name.replace('\\', '/')))
smap = {int(k): v for k, v in json.load(open(os.path.join(ROOT, 'work/render/dlc_shader_map.json'))).items()}
L = pickle.load(open(os.path.join(ROOT, 'work/render/shaderlibs.pkl'), 'rb'))
rows = []
for i in sorted(libs):
    m = smap.get(i)
    lib = L['D'].get(i) or L['X'].get(i)
    rows.append(dict(id=i, cls=m['cls'] if m else None, kind=lib['kind'] if lib else None, nentries=len(lib['entries']) if lib else None,
                     nslots=len([s for s in lib['slots'] if s != 0xffffffff]) if lib else None, in_base=i in L['X'], drms=sorted(libs[i])))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out'); os.makedirs(OUT, exist_ok=True)
json.dump(rows, open(os.path.join(OUT, 'census.json'), 'w'))
print('packs', dict(allpacks))
print('DLC1 distinct type-9 ids', len(rows))
print('by class', collections.Counter(r['cls'] for r in rows))
print('by kind (0=VS,1=PS)', collections.Counter(r['kind'] for r in rows))
print('by class,kind', collections.Counter((r['cls'], r['kind']) for r in rows))
print('entries (distinct blobs) total in non-A/B', sum(r['nentries'] for r in rows if r['cls'] not in ('A', 'B') and r['nentries']))
print('slots total in non-A/B', sum(r['nslots'] for r in rows if r['cls'] not in ('A', 'B') and r['nslots']))
