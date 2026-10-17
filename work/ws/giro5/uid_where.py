import sys, os, json, struct, glob
sys.path.insert(0, '/path/to/trudlcport/tools')
import drm, unit_ids as U
R = '/path/to/trudlcport/work/baseline/B87_materiali19/mods/'
want = {9392, 9397, 9395, 9396, 6713, 29392, 29397, 29395, 29396, 26713}
base = json.load(open('/path/to/trudlcport/work/ws/giro5/base_uids.json'))
for k, ids in base.items():
    h = want & set(ids)
    if h: print('PC base unit', k, sorted(h))
for p in sorted(glob.glob(R + '**/*.drm', recursive=True)):
    try: sc = drm.sections_with_data(drm.cdrm_decode(open(p, 'rb').read(), 'le'), 'le')[1]; Lv = U.level_info(sc, 'le')
    except Exception: continue
    if not Lv or not Lv['intros']: continue
    ids = [struct.unpack_from('<I', sc[si]['data'], o + 0x58)[0] for si, o in Lv['intros']]
    h = want & set(ids)
    if h: print('DLC B87 unit', os.path.relpath(p, R), sorted(h), 'intros', len(ids))
