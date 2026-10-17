"""Texel reali (colore medio RGBA del mip 0, cubi = media delle 6 facce) per TUTTE le texture, PC e Xbox vergine. Nessun grigio di ripiego.
PC : sezione tipo 5 dei DRM della baseline (DLC) oppure del gioco base (idx_pc.json); decodifica tex_convert.pc_image (DXT1/3/5/ARGB).
Xbox: sezione tipo 5 dei DRM Xbox DLC (idx_dlc.json) o base (idx_xbox_base.json); decodifica tex_convert.xbox_levels (de-tiling) + decode_blocks;
      DXN -> (ch0, ch1, 0, 1) come lo restituisce l'Xbox al fetch (il PC la tiene come DXT5 R=ch0, A=ch1).
Uso come libreria: import texlib; texlib.set_baseline('B87_materiali19'); texlib.pc_mean(tid) / texlib.xb_mean(tid)."""
import sys, os, json, struct, glob, functools
import numpy as np
ROOT = '/path/to/trudlcport'
sys.path.insert(0, ROOT + '/tools')
import drm, tex_convert as TC
from archive import Archive

_idx = {}
def _build_idx(path):
    d = json.load(open(path)); r = {}
    for e in d:
        if not isinstance(e[5], list): continue
        for s in e[5]:
            if s[0] == 5: r.setdefault(s[1], (e[0], e[1]))
    return r
IX = {'dlc': _build_idx(ROOT + '/work/idx_dlc.json'), 'xb': _build_idx(ROOT + '/work/idx_xbox_base.json'), 'pc': _build_idx(ROOT + '/work/idx_pc.json')}
_arch = {}
def _from_arch(src, tid, endian):
    path, i = IX[src][tid]
    if path not in _arch: _arch[path] = Archive(path, endian)
    a = _arch[path]
    raw = drm.cdrm_decode(a.read(a.idx[i]), endian)
    return [s for s in drm.sections_with_data(raw, endian)[1] if s['type'] == 5 and s['id'] == tid][0]['data']

_BASE = {'name': None, 'secs': None}
def set_baseline(name):
    """Indice id texture -> (file, indice sezione) sui DRM della baseline (letti una volta, cache pickle)."""
    cache = ROOT + '/work/ws/giro5/texidx_%s.json' % name
    base = ROOT + '/work/baseline/%s/mods' % name
    if os.path.exists(cache): idx = {int(k): tuple(v) for k, v in json.load(open(cache)).items()}
    else:
        idx = {}
        for p in sorted(glob.glob(base + '/**/*.drm', recursive=True)):
            try: sc = drm.sections_with_data(drm.cdrm_decode(open(p, 'rb').read(), 'le'), 'le')[1]
            except Exception: continue
            for s in sc:
                if s['type'] == 5: idx.setdefault(s['id'], (os.path.relpath(p, base), s['i']))
        json.dump({str(k): v for k, v in idx.items()}, open(cache, 'w'))
    _BASE['name'] = name; _BASE['idx'] = idx; _BASE['base'] = base; _BASE['cache'] = {}

def pc_sec(tid):
    """bytes della sezione texture PC: prima la baseline (DLC), poi il gioco base."""
    if _BASE['name'] and tid in _BASE['idx']:
        rel, si = _BASE['idx'][tid]
        if rel not in _BASE['cache']:
            _BASE['cache'][rel] = drm.sections_with_data(drm.cdrm_decode(open(_BASE['base'] + '/' + rel, 'rb').read(), 'le'), 'le')[1]
        s = _BASE['cache'][rel][si]
        assert s['id'] == tid and s['type'] == 5
        return s['data'], 'dlc:' + rel
    if tid in IX['pc']: return _from_arch('pc', tid, 'le'), 'base'
    return None, None

def xb_sec(tid):
    for src in ('dlc', 'xb'):
        if tid in IX[src]: return _from_arch(src, tid, 'be'), src
    return None, None

def _mean_img(imgs):
    return np.mean([im.reshape(-1, 4).astype(np.float64).mean(0) for im in imgs], axis=0) / 255.0

@functools.lru_cache(maxsize=None)
def pc_mean(tid):
    d, src = pc_sec(tid)
    if d is None: return None
    h = TC.parse_pc(d); kind = TC.pc_kind(h['fmt']); cube = bool(h['flags'] & 0x8000)
    faces = 6 if cube else 1
    m = _mean_img([TC.pc_image(d, f, 0) for f in range(faces)])
    if kind == 'DXT1': m[3] = 1.0 if True else m[3]
    if kind == 'ARGB' and False: pass
    return dict(kind=kind, cube=cube, w=h['w'], h=h['h'], rgba=m, src=src)

@functools.lru_cache(maxsize=None)
def xb_mean(tid):
    d, src = xb_sec(tid)
    if d is None: return None
    h, res, _ = TC.xbox_levels(d)
    name = h['fmtname']; cube = bool(h['flags'] & 0x8000)
    kind = {'DXT1': 'DXT1', 'DXT2_3': 'DXT3', 'DXT4_5': 'DXT5', 'DXN': 'DXN', '8_8_8_8': 'ARGB'}.get(name)
    if kind is None or not h['tiled']: return dict(kind=name, cube=cube, w=h['w'], h=h['h'], rgba=None, src=src)
    imgs = []
    for face in res:
        blk = face[0]
        if kind == 'ARGB':   # Xbox 8_8_8_8 dopo lo swap endian: ARGB big-endian -> la conversione ufficiale lo tiene com'e' (BGRA PC)
            imgs.append(TC.blocks_to_image(blk, 'ARGB', h['w'], h['h']))
        else:
            imgs.append(TC.blocks_to_image(blk, kind, h['w'], h['h']))
    m = _mean_img(imgs)
    if kind == 'DXT1': m[3] = 1.0
    if kind == 'DXN': m = np.array([m[0], m[1], 0.0, 1.0])
    return dict(kind=kind, cube=cube, w=h['w'], h=h['h'], rgba=m, src=src)

def pc_texel(tid):
    """RGBA medio che il PC restituisce al fetch (DXN convertita in DXT5: R=ch0, G=1, B=0, A=ch1, cosi' com'e')."""
    m = pc_mean(tid); return None if m is None else m['rgba']

def xb_texel(tid):
    m = xb_mean(tid); return None if m is None else m['rgba']

if __name__ == '__main__':
    set_baseline('B87_materiali19')
    for a in sys.argv[1:]:
        t = int(a); p = pc_mean(t); x = xb_mean(t)
        print(t, 'PC', None if p is None else (p['kind'], 'cubo' if p['cube'] else '2D', p['w'], p['h'], np.round(p['rgba'], 3), p['src']),
              '| Xbox', None if x is None else (x['kind'], 'cubo' if x['cube'] else '2D', np.round(x['rgba'], 3) if x['rgba'] is not None else None, x['src']))
