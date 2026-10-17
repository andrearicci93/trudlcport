"""Script Symbol id map (cdc::Symbol, u16) Xbox -> PC, stored as pseudo type 100 in work/generic/idmap.json.

seed   : ScriptTypeStreamData.m_name (2 x u16 Symbol @ offset 8 of every Script section root), all matched pairs
harvest: words whose learned class is id16*:100 (symbol fields) contribute (xsym -> pcsym) votes;
         majority wins, entries that would break injectivity are dropped.
Usage: python3 -I tools/generic_symbols.py seed|bootstrap|harvest
  seed      : DESTRUCTIVE rebuild of key '100' from script names + 1 harvest round (the original method)
  bootstrap : add symbols from raw u16-half votes (near-monotone constrained) to the current map
  harvest   : add symbols from words whose learned class is a symbol class (needs mask_table.pkl)
"""
import sys, os, struct, pickle, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_reloc as R
import generic_learn as G
from generic_ids import section_matches
W = G.W

def seed(P, idm):
    v = collections.defaultdict(collections.Counter)
    for nm, (x, p) in P.items():
        sx, sp = x[1], p[1]
        for i, j, _ in section_matches(sx, sp, idm):
            a, b = sx[i], sp[j]
            if a['type'] != 8 or a['size'] < 12 or a['size'] != b['size']: continue
            xa, xb = struct.unpack_from('>HH', a['data'], 8); pa, pb = struct.unpack_from('<HH', b['data'], 8)
            v[xa][pa] += 1; v[xb][pb] += 1
    return v

def harvest(P, idm, T, types=(7, 8)):
    v = collections.defaultdict(collections.Counter)
    for nm, (x, p) in P.items():
        sx, sp = x[1], p[1]
        labs = G.drm_labels(sx, 'be', types)
        for i, j, _ in section_matches(sx, sp, idm):
            a, b = sx[i], sp[j]
            if a['type'] not in types or a['size'] != b['size']: continue
            for w, key, ck in G.word_keys(a["size"], labs[i]):
                c, _ = G.lookup(T, key, ck)
                if not c or not c.startswith('id16') or not c.endswith(':%d' % G.SYM): continue
                xa, xb = struct.unpack_from('>HH', a['data'], w); pa, pb = struct.unpack_from('<HH', b['data'], w)
                which = c[4:].split(':')[0]
                if 'a' in which and xa != 0xffff: v[xa][pa] += 1
                if 'b' in which and xb != 0xffff: v[xb][pb] += 1
    return v

XS_MAX, PS_MAX = 20000, 17000     # symbol ranges seen in script names: Xbox base 16347 / TU 19634, PC 16828

def raw_votes(P, idm, types=(7, 8)):
    """Bootstrap: every non-pointer/non-id word of an equal-size matched pair where one u16 half is equal
    (as a value, i.e. u16-swapped) and the other differs gives a (xsym -> pcsym) candidate; a word whose
    two halves are both equal pairs (A,A)->(PA,PA) votes A->PA (paired-symbol words)."""
    v = collections.defaultdict(collections.Counter)
    for nm, (x, p) in P.items():
        sx, sp = x[1], p[1]
        for i, j, _ in section_matches(sx, sp, idm):
            a, b = sx[i], sp[j]
            if a['type'] not in types or a['size'] != b['size'] or a['data'] is None: continue
            rel = R.parse(a['reloc'], 'be')
            skip = set(rel.pointer_offsets()) | set(rel.id_offsets())
            da, db = a['data'], b['data']
            for w in range(0, len(da) // 4 * 4, 4):
                if w in skip or da[w:w + 4] == db[w:w + 4]: continue
                xa, xb = struct.unpack_from('>HH', da, w); pa, pb = struct.unpack_from('<HH', db, w)
                bs = lambda u: ((u & 0xff) << 8) | (u >> 8)
                ok = lambda xs, ps: xs != ps and 0 < xs < XS_MAX and 0 < ps < PS_MAX and ps != bs(xs)
                if xa == pa and ok(xb, pb): v[xb][pb] += 1
                elif xb == pb and ok(xa, pa): v[xa][pa] += 1
                elif xa == xb and pa == pb and ok(xa, pa): v[xa][pa] += 2
    return v

def monotone_ok(m, ks, xs, ps):
    """ps fits between the mapped values of the nearest mapped neighbours of xs (near-monotone map)."""
    import bisect
    k = bisect.bisect_left(ks, xs)
    lo = m[ks[k - 1]] if k > 0 else -1
    hi = m[ks[k]] if k < len(ks) and ks[k] != xs else (m[ks[k + 1]] if k + 1 < len(ks) else 1 << 20)
    if k < len(ks) and ks[k] == xs: return m[xs] == ps
    pa = m[ks[k - 1]] + (xs - ks[k - 1]) if k > 0 else None
    pb = m[ks[k]] - (ks[k] - xs) if k < len(ks) else None
    return ps in (pa, pb) or lo < ps < hi

def bootstrap(seed_map, votes, min_votes=2, min_share=0.6, rounds=6, strong=4):
    m = dict(seed_map)
    for r in range(rounds):
        ks = sorted(m); used = set(m.values()); add = {}
        for xs, c in votes.items():
            if xs in m: continue
            (ps, n), = c.most_common(1)
            if n < min_votes or n < min_share * sum(c.values()) or ps in used or not (0 < xs < XS_MAX and 0 < ps < PS_MAX): continue
            if monotone_ok(m, ks, xs, ps) or (n >= strong and n >= 0.8 * sum(c.values())): add[xs] = ps
        best = {}
        for k, v in add.items():          # PC symbol claimed by several Xbox symbols: strongest vote wins
            n = votes[k][v]
            if v not in best or n > best[v][1]: best[v] = (k, n)
        add = {k: v for v, (k, n) in best.items()}
        if not add: break
        m.update(add)
        print('bootstrap round', r, 'added', len(add), 'total', len(m))
    return m

def interpolate(m, xs_list):
    """Fill symbols lying strictly inside a consistent span (m[b]-m[a] == b-a): exact in leave-one-out
    (4731/4731).  Returns {xs: ps} for the filled ones."""
    import bisect
    ks = sorted(m); out = {}
    for xs in xs_list:
        if xs in m: continue
        k = bisect.bisect_left(ks, xs)
        if 0 < k < len(ks):
            a, b = ks[k - 1], ks[k]
            if m[b] - m[a] == b - a: out[xs] = m[a] + xs - a
    return out

def resolve(votes, min_share=0.6):
    m = {}
    for xs, c in votes.items():
        (ps, n), = c.most_common(1)
        if n >= min_share * sum(c.values()): m[xs] = ps
    inv = collections.Counter(m.values())
    return {k: v for k, v in m.items() if inv[v] == 1}

def save(symmap):
    path = os.path.join(W, 'idmap.json')
    d = json.load(open(path))
    d[str(G.SYM)] = {str(a): b for a, b in symmap.items()}
    json.dump(d, open(path, 'w'))

if __name__ == '__main__' and sys.argv[1:2] == ['harvest']:
    # add symbols voted by words whose LEARNED class is a symbol class (needs a trained mask_table.pkl)
    from convert_generic import IdMapper
    from generic_cache import load_pairs
    P = load_pairs(); idm = IdMapper().m
    T = G.Table(); v, n = pickle.load(open(os.path.join(W, 'mask_table.pkl'), 'rb')); T.v.update(v); T.n.update(n)
    hv = harvest(P, idm, T)
    m = dict(idm.get(G.SYM, {}))
    m2 = bootstrap(m, hv)
    print('harvest: %d -> %d symbols' % (len(m), len(m2)))
    save(m2)
    sys.exit()

if __name__ == '__main__' and sys.argv[1:2] == ['bootstrap']:
    from convert_generic import IdMapper
    from generic_cache import load_pairs
    P = load_pairs()
    idm = IdMapper().m
    base = idm.get(G.SYM, {})
    rv = raw_votes(P, idm)
    print('raw vote symbols', len(rv), 'seed', len(base))
    m = bootstrap(base, rv)
    # sanity: leave-one-out of monotone interpolation on the final map
    ks = sorted(m); ok = tot = 0
    for k in range(1, len(ks) - 1):
        a, x, b = ks[k - 1], ks[k], ks[k + 1]
        if m[b] - m[a] == b - a: tot += 1; ok += m[a] + x - a == m[x]
    print('interpolation LOO on final map: %d/%d' % (ok, tot))
    save(m)
    sys.exit()

if __name__ == '__main__' and sys.argv[1:2] == ['seed']:   # DESTRUCTIVE: rebuilds key 100 from names + 1 harvest
    from convert_generic import IdMapper
    from generic_cache import load_pairs
    P = load_pairs()
    idm = IdMapper().m
    sv = seed(P, idm)
    s0 = resolve(sv)
    print('seed symbols', len(s0), 'conflicting', sum(1 for c in sv.values() if len(c) > 1))
    idm[G.SYM] = s0
    names = sorted(P)
    T = G.train(P, names, idm, types=(7, 8))
    hv = harvest(P, idm, T)
    for k, c in sv.items(): hv[k].update({kk: vv * 10 for kk, vv in c.items()})
    s1 = resolve(hv)
    print('after harvest', len(s1), 'symbols; seed entries changed:', sum(1 for k in s0 if s1.get(k) != s0[k]))
    save(s1)
