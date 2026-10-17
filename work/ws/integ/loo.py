"""loo.py - leave-one-DRM-out analysis of generic_type0.lookup() tie handling (REPORT.md (e)).
For type T in (7, 0): global table = train over ALL base pairs; for every base DRM d the LOO view = global - local(d), then every word of d
(matched A/K sections, same size, informative-or-not, classes as in training) is converted with lookup variants and compared with the real PC word
(correct <=> chosen class in the word's explaining class list cs).  Variants:
  cur    : generic_type0.lookup as is
  b3     : shape B3 (0x000000XX) AND result not from a shape tier (S/SC) AND class in raw/b2s16/s16b2  -> s32
  b3all  : same but any class != s32 -> s32
  tie    : S and SC tiers are skipped when their top two BASIC classes tie (>0)
  tie+b3 : both
Usage: python -I loo.py TYPE [max_names]"""
import sys, os, struct, collections, time, pickle
sys.path.insert(0, os.path.expanduser('~/Downloads/tru-port/tools'))
import generic_type0 as G0, generic_learn as G, drm_reloc as R
from generic_cache import load_pairs
from generic_ids import section_matches
BASIC = ('s32', 's16', 'raw', 'b2s16', 's16b2')
K_MIN = G0.K_MIN
def best_c(c):
    if not c: return None
    tot = sum(c.values())
    items = [kv for kv in c.items() if kv[0] != '?' and not kv[0].startswith('K:')]
    k = [kv for kv in c.items() if kv[0].startswith('K:')]
    if k:
        kb = max(k, key=lambda kv: kv[1])
        if kb[1] >= K_MIN and kb[1] >= 0.9 * tot: return kb[0]
    if not items: return None
    return max(items, key=lambda kv: (kv[1], -G.PREF.get(kv[0], 9)))[0]
def tied(c):
    if not c: return False
    v = sorted((c.get(b, 0) for b in BASIC), reverse=True)
    return v[0] > 0 and v[0] == v[1]
class View:
    def __init__(s, Gt, L): s.G, s.L, s.cache = Gt, L, {}
    def counter(s, k):
        c = s.G.v.get(k); l = s.L.v.get(k)
        if not c: return None
        if l: c = c - l
        return c if c else None
    def best(s, k):
        if k not in s.cache: s.cache[k] = best_c(s.counter(k))
        return s.cache[k]
    def tied(s, k):
        return tied(s.counter(k))
def lookup_v(V, key, ck, xw, skip_tied=False):
    sh = G0.shape(xw)
    for tk, src in ((('S', key, sh), 'shape'), (('SC',) + ck + (sh,), 'shape-coarse')):
        if skip_tied and V.tied(tk): continue
        c = V.best(tk)
        if c is not None: return c, src
    for k, src in ((key, 'label'), (G.mid(key), 'mid'), (('C',) + ck, 'coarse')):
        c = V.best(k)
        if c is not None: return c, src
    c = V.best(('SG', sh))
    if c in ('s32', 's16', 'b2s16', 's16b2'): return c, 'shape-global'
    c = V.best(('R', key[0]))
    if c is not None: return c, 'region'
    return None, 'fallback'
def sections(P, nm, idm, t):
    (xh, sx), (ph, sp) = P[nm]; labs = None
    for i, j, stg in section_matches(sx, sp, idm):
        a, b = sx[i], sp[j]
        if a['type'] != t or a['size'] != b['size'] or a['data'] is None or stg not in ('A', 'K'): continue
        if labs is None: labs = G0.labels(sx, 'be', (t,))
        rel = R.parse(a['reloc'], 'be'); skip = set(rel.pointer_offsets()) | set(rel.id_offsets())
        yield i, a['data'], b['data'], labs[i], skip
def local_train(P, nm, idm, t):
    L = G0.Table0()
    for i, da, db, lab, skip in sections(P, nm, idm, t):
        for w, key, ck in G.word_keys(len(da), lab):
            if w in skip: continue
            cs = G0.word_classes0(da[w:w + 4], db[w:w + 4], idm)
            if cs is None: continue
            sh = G0.shape(da[w:w + 4])
            for k in (key, G.mid(key), ('R', key[0]), ('C',) + ck, ('S', key, sh), ('SC',) + ck + (sh,), ('SG', sh)): L.add(k, cs)
    return L
def main(t, maxn=None):
    P = load_pairs(); idm = G0.idmaps(); names = sorted(P)
    if maxn: names = names[:maxn]
    t0 = time.time(); Gt = G0.Table0(); locs = {}
    # pass 1: global table (+ per-DRM local kept only as keys-to-subtract: recomputed in pass 2)
    for nm in names:
        L = local_train(P, nm, idm, t)
        for k, c in L.v.items(): Gt.v[k].update(c)
    print('trained', t, len(names), 'DRMs, keys', len(Gt.v), '%.0fs' % (time.time() - t0), flush=True)
    st = collections.Counter(); ex = collections.defaultdict(list)
    for nm in names:
        L = local_train(P, nm, idm, t); V = View(Gt, L)
        for i, da, db, lab, skip in sections(P, nm, idm, t):
            for w, key, ck in G.word_keys(len(da), lab):
                if w in skip: continue
                xw, pw = da[w:w + 4], db[w:w + 4]
                if struct.unpack('>I', xw)[0] in G0.VMAP: continue
                cs = G0.word_classes0(xw, pw, idm)
                if cs is None: continue
                sh = G0.shape(xw)
                res = {}
                for var, skt in (('cur', False), ('tie', True)):
                    c, src = lookup_v(V, key, ck, xw, skt)
                    if c is None: c = 'raw' if G.is_text(xw) and xw != xw[::-1] else 's32'; src = 'fallback'
                    res[var] = (c, src)
                for base in ('cur', 'tie'):
                    c, src = res[base]
                    c1 = 's32' if (sh == 'B3' and src not in ('shape', 'shape-coarse') and c in ('raw', 'b2s16', 's16b2')) else c
                    c2 = 's32' if (sh == 'B3' and src not in ('shape', 'shape-coarse') and c != 's32') else c
                    res['b3' if base == 'cur' else 'tie+b3'] = (c1, src)
                    if base == 'cur': res['b3all'] = (c2, src)
                cc, src = res['cur']; ok = {v: (r[0] in cs) for v, r in res.items()}
                st['words'] += 1
                st['cur_wrong'] += not ok['cur']
                st['cur_wrong', src, sh] += not ok['cur']; st['n', src, sh] += 1
                for v in ('b3', 'b3all', 'tie', 'tie+b3'):
                    if res[v][0] != cc:
                        st[v, 'changed'] += 1
                        if (not ok['cur']) and ok[v]: st[v, 'fixed'] += 1
                        if ok['cur'] and not ok[v]: st[v, 'regressed'] += 1; ex[v].append((nm, i, hex(w), xw.hex(), pw.hex(), cc, res[v][0], src, sh))
                        if (not ok['cur']) and (not ok[v]): st[v, 'both_wrong'] += 1
                    st[v, 'wrong'] += not ok[v]
    print('=== type', t, 'LOO over', len(names), 'DRMs, words', st['words'], 'cur wrong words', st['cur_wrong'], '%.0fs' % (time.time() - t0))
    for v in ('b3', 'b3all', 'tie', 'tie+b3'):
        print(v, 'changed', st[v, 'changed'], 'fixed', st[v, 'fixed'], 'regressed', st[v, 'regressed'], 'both_wrong', st[v, 'both_wrong'], 'total wrong', st[v, 'wrong'])
    print('cur wrong by (src, shape) top:')
    for k, v in sorted(((k, v) for k, v in st.items() if isinstance(k, tuple) and k[0] == 'cur_wrong' and len(k) == 3), key=lambda kv: -kv[1])[:14]:
        print('   ', k[1:], 'wrong', v, 'of', st['n', k[1], k[2]])
    for v in ex: print(v, 'regression examples', ex[v][:6])
    pickle.dump((dict(st), dict(ex)), open('loo_%d.pkl' % t, 'wb'))
if __name__ == '__main__':
    main(int(sys.argv[1]), int(sys.argv[2]) if len(sys.argv) > 2 else None)
