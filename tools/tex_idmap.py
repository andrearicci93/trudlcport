"""Content-based Xbox->PC TEXTURE id map (the positional 'C' matches of generic_ids mis-pair textures that the PC
build reordered; e.g. g_pda Xbox 534..538 -> PC 701..705 rotated by one, PSNR 4-17 dB instead of exact).

For every Xbox<->PC DRM pair (bigfile pairs + patch.000 pairs): tex_convert.convert(Xbox texture) is compared with the
PC textures of the same DRM: byte-identical -> strong vote (10); else best PSNR >= 35 dB among same-size PC textures ->
weak vote (1). Final: per Xbox id the PC id with most votes, injective (strongest wins). Entries replace idmap['5'];
Xbox ids without content evidence keep the old mapping unless their PC id was claimed by a content match (then dropped).
Usage: tools/venv/bin/python -I tools/tex_idmap.py   (rewrites key '5' of work/generic/idmap.json, backup *_pre_tex.json)
"""
import sys, os, json, hashlib, collections, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from multiprocessing import Pool
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work', 'generic')

def work(args):
    name, src = args
    import numpy as np, tex_convert as T
    if src == 'base':
        from pairs import pc_drm, xbox_drm
        x, p = xbox_drm(name), pc_drm(name)
    else:
        import override_merge as OM
        try:
            x = (None, OM.load(('tu', 'xl1', 'xl2'), name)[2]); p = (None, OM.load(('pcpatch',), name)[2])
        except FileNotFoundError:
            return []
    if not x or not p: return []
    ps = [s for s in p[1] if s['type'] == 5]
    byhash = collections.defaultdict(list)
    for s in ps: byhash[hashlib.sha1(s['data']).digest()].append(s['id'])
    imgs = {}
    out = []
    for s in x[1]:
        if s['type'] != 5: continue
        try:
            c = T.convert(s['data'])
        except Exception:
            continue
        h = hashlib.sha1(c).digest()
        if h in byhash:
            for pid in byhash[h]: out.append((s['id'], pid, 10))
            continue
        try:
            ci = np.asarray(T.pc_image(c), dtype=np.float32)
        except Exception:
            continue
        best = (0, None)
        for q in ps:
            if q['id'] not in imgs:
                try: imgs[q['id']] = np.asarray(T.pc_image(q['data']), dtype=np.float32)
                except Exception: imgs[q['id']] = None
            qi = imgs[q['id']]
            if qi is None or qi.shape != ci.shape: continue
            e = float(((qi - ci) ** 2).mean())
            v = 99.0 if e == 0 else 10 * np.log10(255 ** 2 / e)
            if v > best[0]: best = (v, q['id'])
        if best[0] >= 35: out.append((s['id'], best[1], 1))
    return out

if __name__ == '__main__':
    from generic_cache import names
    jobs = [(n, 'base') for n in names()] + [(n, 'patch') for n in ('g_pda.drm', 'l2_puzzleroom.drm')]
    votes = collections.defaultdict(collections.Counter)
    with Pool(8) as pool:
        for res in pool.imap_unordered(work, jobs, chunksize=2):
            for x, p, w in res: votes[x][p] += w
    m = {}
    for x, c in votes.items(): m[x] = c.most_common(1)[0][0]
    inv = collections.defaultdict(list)
    for x, p in m.items(): inv[p].append(x)
    for p, xs in inv.items():
        if len(xs) > 1:
            keep = max(xs, key=lambda x: votes[x][p])
            for x in xs:
                if x != keep: del m[x]
    path = os.path.join(W, 'idmap.json')
    d = json.load(open(path)); old = {int(k): v for k, v in d['5'].items()}
    claimed = set(m.values())
    new = dict(m)
    kept = 0
    for x, p in old.items():
        if x not in new and p not in claimed: new[x] = p; kept += 1
    changed = sum(1 for x, p in m.items() if old.get(x) != p)
    print('content-voted xids %d (changed vs old %d), old kept without evidence %d, dropped %d, total %d' % (
        len(m), changed, kept, len(old) - kept - sum(1 for x in old if x in m), len(new)))
    shutil.copy(path, path.replace('.json', '_pre_tex.json'))
    d = json.load(open(path)); d['5'] = {str(k): v for k, v in sorted(new.items())}
    json.dump(d, open(path, 'w'))
    print('updated', path)
