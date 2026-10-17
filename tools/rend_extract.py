"""Extract render sections (types 9 Shader, 10 Material, 12 Mesh) of all Xbox<->PC base pairs and of DLC DRMs
into pickles under work/render/ (one file per set) for fast analysis.
usage: python3 -I tools/rend_extract.py pairs|dlc"""
import sys, json, pickle, os
sys.path.insert(0, '/path/to/trudlcport/tools')
from multiprocessing import Pool
from rend_common import WORK, ROOT
TYPES = (9, 10, 12)
def slim(drm):
    if drm is None: return None
    h, secs = drm
    return [dict(i=s['i'], type=s['type'], id=s['id'], size=s['size'], ver=s['ver'], flags=s['flags'], spec=s['spec'],
                 reloc=s['reloc'] if s['type'] in TYPES else b'', data=s['data'] if s['type'] in TYPES else b'') for s in secs]
def work_pair(nm):
    from pairs import xbox_drm, pc_drm
    try: return nm, slim(xbox_drm(nm)), slim(pc_drm(nm))
    except Exception as ex: return nm, None, repr(ex)
def work_dlc(job):
    path, i = job
    from archive import Archive
    from drm import cdrm_decode, sections_with_data
    a = Archive(path, 'be')
    r = a.idx[i]
    raw = cdrm_decode(a.read(r), 'be')
    return path, i, r['hash'], slim(sections_with_data(raw, 'be'))
if __name__ == '__main__':
    what = sys.argv[1]
    if what == 'pairs':
        names = json.load(open(WORK + 'pairnames.json'))
        with Pool(8) as p: res = p.map(work_pair, names, chunksize=4)
        pickle.dump(res, open(WORK + 'pairs_render.pkl', 'wb'))
        print(len(res), 'pairs; failures', sum(1 for r in res if r[1] is None or not isinstance(r[2], list)))
    else:
        idx = json.load(open(ROOT + 'work/idx_dlc.json'))
        jobs = [(r[0], r[1]) for r in idx if isinstance(r[5], list)]
        with Pool(8) as p: res = p.map(work_dlc, jobs, chunksize=4)
        pickle.dump(res, open(WORK + 'dlc_render.pkl', 'wb'))
        print(len(res), 'dlc drms')
