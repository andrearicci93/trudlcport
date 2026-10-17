"""Section stores used by the DLC generic converter.

  pc_ids    {type: set(id)}  every section id present in any PC DRM (bigfile index + patch.000)
  pc_store  {(type, pc_id): rec}  PC section content for generic types (2,7,8,11) from the pair cache,
            rec = dict(data, reloc(LE blob), ext=[(type,id) target of each external reloc], ver, flags, src)
            For ids with several contents the patch.000 version wins (runtime authoritative), else the most
            frequent one.
  xb_hash   {(type, xbox_id): set(normalised hash)}  Xbox base contents (layers + TitleUpdate)
  xb_store  {(type, xbox_id): dict(data, reloc, src)}  one Xbox base content per id (template source)
normalised hash = md5 over (internal relocs, external relocs as (target type,id,src,dst), idrefs, data):
section-index independent, so the same section in two DRMs hashes equal.
Usage: python3 -I tools/generic_store.py  -> work/generic/store.pkl
"""
import sys, os, json, pickle, hashlib, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_reloc as R
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work', 'generic')
STORE = os.path.join(W, 'store.pkl')
GENERIC = (2, 7, 8, 11)

def norm_hash(s, secs, endian):
    r = R.parse(s['reloc'], endian)
    ext = tuple((secs[si]['type'], secs[si]['id'], so, do) for si, so, do in r.external)
    return hashlib.md5(repr((r.internal, ext, r.idref, r.idref_a)).encode() + s['data']).hexdigest()

def build():
    from generic_cache import load_pairs
    P = load_pairs()
    pc_ids = collections.defaultdict(set)
    for rec in json.load(open(os.path.join(W, '..', 'idx_pc.json'))):
        if isinstance(rec[5], list):
            for t, i, *_ in rec[5]: pc_ids[t].add(i)
    for nm, (x, p) in P.items():
        for s in p[1]: pc_ids[s['type']].add(s['id'])
    cand = collections.defaultdict(collections.Counter); recs = {}
    xb = collections.defaultdict(set); xb_store = {}
    for nm, (x, p) in P.items():
        for s in x[1]:
            if s['type'] in GENERIC and s['data'] is not None:
                xb[s['type'], s['id']].add(norm_hash(s, x[1], 'be'))
                rec = dict(data=s['data'], reloc=s['reloc'], src=nm)
                if nm.startswith('patch:'): xb_store[s['type'], s['id']] = rec      # TU content wins
                else: xb_store.setdefault((s['type'], s['id']), rec)
        for s in p[1]:
            if s['type'] not in GENERIC or s['data'] is None: continue
            h = norm_hash(s, p[1], 'le')
            k = (s['type'], s['id'])
            cand[k][h] += 1000000 if nm.startswith('patch:') else 1
            if h not in recs:
                r = R.parse(s['reloc'], 'le')
                recs[h] = dict(data=s['data'], reloc=s['reloc'], ext=[(p[1][si]['type'], p[1][si]['id']) for si, _, _ in r.external],
                               ver=s['ver'], flags=s['flags'], src=nm)
    pc_store = {k: recs[c.most_common(1)[0][0]] for k, c in cand.items()}
    multi = sum(1 for c in cand.values() if len(c) > 1)
    pickle.dump(dict(pc_ids={t: v for t, v in pc_ids.items()}, pc_store=pc_store, xb_hash=dict(xb), xb_store=xb_store), open(STORE, 'wb'))
    print('pc_ids', {t: len(v) for t, v in sorted(pc_ids.items())}, 'pc_store', len(pc_store), 'multi-content PC ids', multi, 'xb', len(xb))

def load():
    return pickle.load(open(STORE, 'rb'))

if __name__ == '__main__':
    build()
