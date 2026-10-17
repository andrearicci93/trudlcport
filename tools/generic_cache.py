"""Build a cache of the 975 Xbox<->PC base DRM pairs (decoded DRM, all reloc blobs,
data of generic section types) -> work/generic/pairs.pkl.
Usage: python3 -I tools/generic_cache.py"""
import sys, pickle, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from archive import Archive
from drm import cdrm_decode, sections_with_data
from names import load, L, crc
from multiprocessing import Pool
BASE = '/path/to/'
KEEP = {0, 1, 2, 3, 4, 7, 8, 10, 11, 13}   # data kept for these types (reloc kept for all)
OUT = BASE + 'tru-port/work/generic/pairs.pkl'

def names():
    pcn = load(L + 'Tomb Raider Underworld (PC).txt')
    pc = Archive(BASE + 'tru-port/pc/bigfile.000', 'le')
    xl = [Archive(BASE + 'TombRaiderUnderworld_Patched/layer1.000', 'be'), Archive(BASE + 'TombRaiderUnderworld_Patched/layer2.000', 'be')]
    pch = {r['hash'] for r in pc.idx}
    xh = {r['hash'] for a in xl for r in a.idx}
    out = []
    for h, n in pcn.items():
        if h in pch and n.lower().startswith('pc-w\\') and n.lower().endswith('.drm'):
            nm = n[5:]
            if crc('xenon-w\\' + nm) in xh: out.append(nm)
    return sorted(out)

def slim(t):
    h, secs = t
    for s in secs:
        if s['type'] not in KEEP: s['data'] = None
    return h, secs

def work(nm):
    import pairs
    try:
        return nm, slim(pairs.xbox_drm(nm)), slim(pairs.pc_drm(nm))
    except Exception as e:
        return nm, None, repr(e)

PATCH_OUT = BASE + 'tru-port/work/generic/pairs_patch.pkl'
# Runtime-authoritative pairs: PC patch.000 overrides bigfile; Xbox TitleUpdate.000 overrides layers
# (the DLC object/unit lists and script ids were built on top of the TU).
PATCH_PAIRS = [('generalbank.drm', 'tu', 'patch'), ('globalsoundinfo.drm', 'tu', 'base'),
               ('l2_puzzleroom.drm', 'base', 'patch'), ('g_pda.drm', 'base', 'patch')]

def build_patch_pairs():
    import pairs
    pp = Archive(BASE + 'tru-port/pc/patch.000', 'le')
    tu = Archive(BASE + 'TombRaiderUnderworld_Patched/TitleUpdate.000', 'be')
    def get(a, nm, e):
        r = a.find(crc(nm)); return sections_with_data(cdrm_decode(a.read(r[0]), e), e)
    out = {}
    for nm, xs, ps in PATCH_PAIRS:
        x = get(tu, 'xenon-w\\' + nm, 'be') if xs == 'tu' else pairs.xbox_drm(nm)
        p = get(pp, 'pc-w\\' + nm, 'le') if ps == 'patch' else pairs.pc_drm(nm)
        out['patch:' + nm] = (slim(x), slim(p))
    pickle.dump(out, open(PATCH_OUT, 'wb'))
    print('wrote', PATCH_OUT, sorted(out))

def load_pairs(patch=True):
    """name -> ((xhdr, xsecs), (pchdr, pcsecs)); with patch=True adds 'patch:<name>' runtime pairs."""
    P = pickle.load(open(OUT, 'rb'))
    if patch and os.path.exists(PATCH_OUT):
        P.update(pickle.load(open(PATCH_OUT, 'rb')))
    return P

if __name__ == '__main__':
    if sys.argv[1:] == ['patch']:
        build_patch_pairs(); sys.exit()
    ns = names()
    print(len(ns), 'pairs')
    with Pool(8) as p: res = p.map(work, ns, chunksize=4)
    bad = [r for r in res if r[1] is None]
    print('errors', len(bad), bad[:3])
    pickle.dump({r[0]: (r[1], r[2]) for r in res if r[1] is not None}, open(OUT, 'wb'))
    print('wrote', OUT, os.path.getsize(OUT))
