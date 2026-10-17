import sys, os, hashlib, json
sys.path.insert(0, 'tools'); sys.path.insert(0, 'work/ws/webs')
import drm_write as DW, build
B8 = 'work/baseline/B8/mods'; B9 = 'work/baseline/B9/mods'; OUT = 'work/ws/webs/out'
B9CH = {'streamgroups/dlc_water_wheel_waterwheel_main.drm', 'dlc_caverns_hall.drm', 'streamgroups/dlc_pillory_pillorymain.drm', 'streamgroups/dlc_pillory_pillory_b.drm'}
rels = []
for dp, dn, fn in os.walk(B8):
    for f in fn:
        if f.endswith('.drm'): rels.append(os.path.relpath(os.path.join(dp, f), B8))
md5 = []; changed = {}
for rel in sorted(rels):
    src = os.path.join(B9 if rel in B9CH else B8, rel)
    raw = DW.cdrm_decode(open(src, 'rb').read(), 'le')
    new, rep = build.patch(raw)
    acts = [r for r in rep if 'skip' not in r[2]]
    if not acts: continue
    A = DW.read(raw, 'le'); N = DW.read(new, 'le')
    ch = [(a.type, a.id) for a, b in zip(A.sections, N.sections) if a.data != b.data or a.reloc != b.reloc]
    assert len(A.sections) == len(N.sections)
    data = DW.cdrm_encode(new, 'le'); dst = os.path.join(OUT, rel); os.makedirs(os.path.dirname(dst), exist_ok=True); open(dst, 'wb').write(data)
    m = hashlib.md5(data).hexdigest(); md5.append('%s  %s' % (m, rel)); changed[rel] = ch
    print(rel, 'src', 'B9' if rel in B9CH else 'B8', rep, 'changed', ch, m)
open(os.path.join(OUT, 'md5.txt'), 'w').write('\n'.join(md5) + '\n')
json.dump({k: v for k, v in changed.items()}, open('work/ws/webs/changed.json', 'w'))
